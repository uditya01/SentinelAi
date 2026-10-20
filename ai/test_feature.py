from ai.feature_utils import basic_file_info

info = basic_file_info("C:/Windows/System32/notepad.exe")

for key, value in info.items():
    print(f"{key}: {value}")