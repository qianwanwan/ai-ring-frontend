import numpy as np
import os
import glob
import json

def calc_intercept_slope(calib_files):
    # load calib points
    pc_timestamps = []
    ring_timestamps = []
    for calib_file in calib_files:
        with open(calib_file, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
            pc_timestamps.extend(data["pc_timestamps"])
            ring_timestamps.extend(data["ring_timestamps"])
    pc_timestamps = np.array(pc_timestamps)
    ring_timestamps = np.array(ring_timestamps)

    # calculate calibration parameters
    X_b = np.c_[np.ones((len(ring_timestamps), 1)), ring_timestamps]
    intercept, slope = np.linalg.inv(X_b.T.dot(X_b)).dot(X_b.T).dot(pc_timestamps)

    return intercept, slope

def ring_time_2_pc_time(ring_time, intercept, slope):
    return intercept + slope * ring_time / 16384

def load_imu_bin(path: str, intercept, slope):
    # 每条记录: 1 个 float64 + 6 个 float32, 小端
    record_dtype = np.dtype([
        ('timestamp', '<f8'),
        ('gyr_x',     '<f8'),
        ('gyr_y',     '<f8'),
        ('gyr_z',     '<f8'),
        ('acc_x',     '<f8'),
        ('acc_y',     '<f8'),
        ('acc_z',     '<f8'),
    ])

    raw = np.fromfile(path, dtype=record_dtype)

    # 转成简单的 ndarray 方便后处理
    timestamps = raw['timestamp']                     # shape: (N,)
    gyr = np.vstack([raw['gyr_x'], raw['gyr_y'], raw['gyr_z']]).T  # (N, 3)
    acc = np.vstack([raw['acc_x'], raw['acc_y'], raw['acc_z']]).T  # (N, 3)

    # sort with timestamps
    sort_idx = np.argsort(timestamps)
    timestamps = timestamps[sort_idx]
    gyr = gyr[sort_idx]
    acc = acc[sort_idx]
    raw = raw[sort_idx]

    # calibrate timestamps
    timestamps = ring_time_2_pc_time(timestamps, intercept, slope)

    return timestamps, gyr, acc, raw

def load_imu_numpy(path: str, intercept, slope):
    data = np.load(path)
    timestamps = data[:, -1]
    acc = data[:, 0:3]
    gyr = data[:, 3:6]
    # calibrate timestamps
    timestamps = ring_time_2_pc_time(timestamps, intercept, slope)

    return timestamps, gyr, acc

def validate_time_calibration(calib_files):
    intercept, slope = calc_intercept_slope(calib_files)
    if not (0.99 <= slope <= 1.001):
        raise ValueError(f"Error: Slope {slope:.6f} is out of expected range (1 ± 0.001).")
    print(f"Slope: {slope:.6f}")
    return intercept, slope

def validate_imu_data(timestamps: np.ndarray, gyr: np.ndarray, acc: np.ndarray):
    # 检查帧率是否在 200 附近
    if len(timestamps) < 2:
        raise ValueError("Not enough data points to validate frame rate.")
    time_diffs = np.diff(timestamps)
    avg_frame_rate = 1.0 / np.mean(time_diffs)
    if not (190 <= avg_frame_rate <= 210):
        raise ValueError(f"Error: Average frame rate {avg_frame_rate:.2f} Hz is out of expected range (200 ± 10 Hz).")
    print(f"Average frame rate: {avg_frame_rate:.2f} Hz")

def validate_log_file(log_file: str):
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if len(lines) == 0:
        raise ValueError(f"Log file {log_file} is empty.")
    num_entries = 0
    num_accepted = 0
    for line in lines:
        try:
            log_entry = eval(line.strip())
            if 'start' not in log_entry:
                raise ValueError(f"Error: Log entry missing 'start' field: {line.strip()}")
            elif 'end' in log_entry:
                num_entries += 1
                if 'qualified' in log_entry and log_entry['qualified']:
                    num_accepted += 1
        except Exception as e:
            raise ValueError(f"Error: cannot parsing log entry: {line.strip()} - {e}")
    print(f"Log file {log_file} validated successfully with {len(lines)} entries.")

if __name__ == '__main__':
    user_id = input("Please input user id: ")
    data_path = os.path.join('records', f'{user_id}')
    imu_files = glob.glob(os.path.join(data_path, '*.npy'))
    time_calibration_files = glob.glob(os.path.join(data_path, '*.json'))
    log_files = glob.glob(os.path.join(data_path, '*.log'))
    assert len(imu_files) > 0, f'Error: No IMU numpy files found in {data_path}'
    assert len(time_calibration_files) > 1, f'Error: Less than 2 time calibration JSON files found in {data_path}'
    assert len(log_files) > 0, f'Error: No log files found in {data_path}'
    intercept, slope = validate_time_calibration(time_calibration_files)
    for idx, imu_file in enumerate(imu_files):
        # ts, gyr, acc, raw = load_imu_bin(imu_file, intercept, slope)
        ts, gyr, acc = load_imu_numpy(imu_file, intercept, slope)
        validate_imu_data(ts, gyr, acc)
        print('imu data', idx, 'samples:', len(ts))
        print('first sample timestamp:', ts[0])
        print('first gyr:', gyr[0])
        print('first acc:', acc[0])
        assert np.all(np.abs(gyr) < 500), f'Error: Gyroscope data out of range in file {imu_file}'
        assert np.all(np.abs(acc) < 500), f'Error: Accelerometer data out of range in file {imu_file}'
    print("校验通过")