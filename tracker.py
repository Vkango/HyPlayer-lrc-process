import os
import csv
import time
from datetime import datetime

class ExperimentTracker:
    def __init__(self, experiment_name, headers):
        """
        初始化实验数据追踪器
        :param experiment_name: 实验名称
        :param headers: 表头内容（列表形式）
        """
        self.experiment_name = experiment_name
        self.headers = headers
        self.data = []
        self.file_path = self._generate_file_path()

    def _generate_file_path(self):
        """
        生成文件路径，确保文件名唯一
        """
        base_dir = "./experiment_data"
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        base_name = f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = os.path.join(base_dir, base_name)

        # 如果文件已存在，添加序号重命名
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(base_dir, f"{self.experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{counter}.csv")
            counter += 1

        return file_path

    def add_data(self, data):
        """
        添加实验数据
        :param data: 数据（字典形式，键需与表头一致）
        """
        if set(data.keys()) != set(self.headers):
            raise ValueError("数据的键与表头不匹配！")
        self.data.append(data)

    def save_data(self):
        """
        将实验数据保存到CSV文件中
        """
        with open(self.file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()
            writer.writerows(self.data)
        print(f"数据已保存到 {self.file_path}")
if __name__ == "__main__":
    experiment_name = "SampleExperiment"
    headers = ["Time", "Temperature", "Pressure", "Humidity"]
    tracker = ExperimentTracker(experiment_name, headers)
    tracker.add_data({
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Temperature": 25.5,
        "Pressure": 101.3,
        "Humidity": 60
    })
    for i in range(3):
        time.sleep(1)
        tracker.add_data({
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Temperature": 25.5 + i,
            "Pressure": 101.3 + i,
            "Humidity": 60 + i
        })
    tracker.save_data()