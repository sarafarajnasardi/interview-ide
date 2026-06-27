import time
import requests

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


JUDGE0_BASE_URL = "https://ce.judge0.com"

LANGUAGE_IDS = {
    "python": 71,
    "c": 50,
    "cpp": 54,
    "java": 62,
}


def normalize_output(value):
    return (value or "").replace("\r\n", "\n").strip()


def get_final_output(result):
    stdout = result.get("stdout") or ""
    stderr = result.get("stderr") or ""
    compile_output = result.get("compile_output") or ""
    message = result.get("message") or ""

    if compile_output:
        return compile_output

    if stderr:
        return stderr

    if message:
        return message

    return stdout


def run_single_test_case(code, language_id, input_data):
    create_response = requests.post(
        f"{JUDGE0_BASE_URL}/submissions/",
        params={
            "base64_encoded": "false",
            "wait": "false",
        },
        json={
            "source_code": code,
            "language_id": language_id,
            "stdin": input_data,
            "cpu_time_limit": 2,
            "memory_limit": 128000,
        },
        timeout=10,
    )

    create_response.raise_for_status()

    token = create_response.json().get("token")

    if not token:
        raise Exception("Judge0 did not return a submission token.")

    result = None

    for _ in range(10):
        result_response = requests.get(
            f"{JUDGE0_BASE_URL}/submissions/{token}",
            params={
                "base64_encoded": "false",
            },
            timeout=10,
        )

        result_response.raise_for_status()
        result = result_response.json()

        status_id = result.get("status", {}).get("id")

        # 1 = In Queue, 2 = Processing
        if status_id not in [1, 2]:
            break

        time.sleep(1)

    if not result:
        raise Exception("No result received from Judge0.")

    return result


@api_view(["POST"])
def run_code(request):
    language = request.data.get("language")
    code = request.data.get("code")
    test_cases = request.data.get("test_cases", [])

    if not language:
        return Response(
            {"status": "error", "message": "Language is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not code:
        return Response(
            {"status": "error", "message": "Code is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    language_id = LANGUAGE_IDS.get(language)

    if not language_id:
        return Response(
            {"status": "error", "message": f"Unsupported language: {language}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not test_cases:
        return Response(
            {"status": "error", "message": "At least one test case is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    test_results = []

    try:
        for index, test_case in enumerate(test_cases, start=1):
            input_data = test_case.get("input", "")
            expected_output = test_case.get("expected_output", "")

            judge_result = run_single_test_case(
                code=code,
                language_id=language_id,
                input_data=input_data,
            )

            judge_status = judge_result.get("status", {}).get("description", "Unknown")
            actual_output = get_final_output(judge_result)

            passed = (
                judge_status == "Accepted"
                and normalize_output(actual_output) == normalize_output(expected_output)
            )

            test_results.append({
                "test_case": index,
                "input": input_data,
                "expected_output": expected_output,
                "actual_output": actual_output,
                "passed": passed,
                "status": judge_status,
                "time": judge_result.get("time"),
                "memory": judge_result.get("memory"),
            })

        passed_all = all(result["passed"] for result in test_results)

        output_lines = []

        for result in test_results:
            output_lines.append(
                f"Test Case {result['test_case']}: "
                f"{'PASSED' if result['passed'] else 'FAILED'}"
            )

            output_lines.append(f"Status: {result['status']}")
            output_lines.append(f"Input:\n{result['input'] or 'No input'}")
            output_lines.append(f"Expected Output:\n{result['expected_output'] or 'No expected output'}")
            output_lines.append(f"Actual Output:\n{result['actual_output'] or 'No output'}")
            output_lines.append("-" * 40)

        final_output = "\n".join(output_lines)

        return Response({
            "status": "success",
            "message": "All test cases passed." if passed_all else "Some test cases failed.",
            "passed_all": passed_all,
            "language": language,
            "output": final_output,
            "test_results": test_results,
        })

    except requests.exceptions.RequestException as error:
        return Response(
            {
                "status": "error",
                "message": "Could not connect to Judge0.",
                "output": str(error),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    except Exception as error:
        return Response(
            {
                "status": "error",
                "message": "Something went wrong while running test cases.",
                "output": str(error),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )