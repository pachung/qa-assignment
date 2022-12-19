#!/usr/bin/env python3
import json
import tarfile
import sys
from pathlib import Path
from warnings import warn


class TestReportGenerator(object):
    """
    Provide functionalities to generate test report from the JSON file inside tar.xz file
    """

    def __init__(self, tar_path):
        if Path.is_absolute(tar_path) is False:
            tar_path = Path.resolve(tar_path)
        self.tarfile_path = tar_path
        self.extract_path = self.tarfile_path.parent.joinpath("extracted_data")
        self.result = {
            "version_of_ubuntu": None,
            "number_of_tests": 0,
            "number_of_skip": 0,
            "number_of_fail": 0,
            "number_of_pass": 0,
            "duration_sum": 0,
        }
        self.result_format = ""

    def extract_tar_file_to_target_path(self, file_to_extract, target_path):
        with tarfile.open(file_to_extract, "r:xz") as tf:
            
            import os
            
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tf, path=target_path)

    def get_json_file_path(self):
        json_file_path = None
        for file in self.extract_path.iterdir():
            if file.suffix == ".json":
                json_file_path = file
                break
        if json_file_path is not None:
            return json_file_path
        else:
            raise FileNotFoundError("Cannot find JSON file from extracted data.")

    def parse_json_from_file(self, file_path=None):
        if file_path is None:
            file_path = self.get_json_file_path()
        with open(file_path, "r") as f:
            parsed_data = json.load(f)
            return parsed_data

    def gather_results(self, json_data):
        self.result["version_of_ubuntu"] = json_data["distribution"]["description"]
        self.result["number_of_tests"] = len(json_data["results"])
        for test in range(self.result["number_of_tests"]):
            test = json_data["results"][test]
            if test["status"] == "skip":
                self.result["number_of_skip"] += 1
            elif test["status"] == "fail":
                self.result["number_of_fail"] += 1
            elif test["status"] == "pass":
                self.result["number_of_pass"] += 1
            else:
                warn(
                    f"Unexpected result's status: {test['status']} in Test ID: {test['id']}"
                )
            self.result["duration_sum"] += test["duration"]

    def prepare_formated_results(self):
        try:
            self.result_format = f"""
{'-'*40}
Version tested: {self.result['version_of_ubuntu']}
Number of tests run: {self.result['number_of_tests']}
Outcome:
\t- skip: {self.result['number_of_skip']} ({self.result['number_of_skip'] / self.result['number_of_tests']:.0%})
\t- fail: {self.result['number_of_fail']} ({self.result['number_of_fail'] / self.result['number_of_tests']:.0%})
\t- pass: {self.result['number_of_pass']} ({self.result['number_of_pass'] / self.result['number_of_tests']:.0%})
Total run duration: {self.result['duration_sum']:.0f} seconds
{'-'*40}
"""
        except ZeroDivisionError as e:
            raise ZeroDivisionError(
                'number_of_tests might be 0. Please check the numbers of "results" in JSON file.'
            ) from e

    def write_test_report_to_file(self, file_path=None):
        if file_path is None:
            file_path = self.extract_path.joinpath("test_report")
        with open(file_path, "w") as f:
            f.write(self.result_format)
        print(f"The test report is generated to the path below:\n '{file_path}'")

    def print_report(self):
        print(self.result_format)

    def generate_report(self):
        self.extract_tar_file_to_target_path(self.tarfile_path, self.extract_path)
        parsed_data = self.parse_json_from_file()
        self.gather_results(parsed_data)
        self.prepare_formated_results()


def get_path_from_argv():
    try:
        return Path(sys.argv[1])
    except IndexError as e:
        raise IndexError(
            "Please make sure to inupt the tarfile path as an argument when executing this script.\n"
            "e.g. '$ python3 test_report_generator.py /path_to_tarfile/submission_TIME.tar.xz'"
        ) from e


def main():
    tar_xz_path = get_path_from_argv()
    generator = TestReportGenerator(tar_xz_path)
    generator.generate_report()
    generator.write_test_report_to_file()
    generator.print_report()


if __name__ == "__main__":
    main()
