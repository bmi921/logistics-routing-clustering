import numpy as np
import pandas as pd


def calc_xy(phi_deg, lambda_deg, phi0_deg, lambda0_deg):
    """緯度経度を平面直角座標に変換する
    - input:
        (phi_deg, lambda_deg): 変換したい緯度・経度[度]（分・秒でなく小数であることに注意）
        (phi0_deg, lambda0_deg): 平面直角座標系原点の緯度・経度[度]（分・秒でなく小数であることに注意）
    - output:
        x: 変換後の平面直角座標[m]
        y: 変換後の平面直角座標[m]
    """
    # 緯度経度・平面直角座標系原点をラジアンに直す
    phi_rad = np.deg2rad(phi_deg)
    lambda_rad = np.deg2rad(lambda_deg)
    phi0_rad = np.deg2rad(phi0_deg)
    lambda0_rad = np.deg2rad(lambda0_deg)

    # 補助関数
    def A_array(n):
        A0 = 1 + (n**2) / 4.0 + (n**4) / 64.0
        A1 = -(3.0 / 2) * (n - (n**3) / 8.0 - (n**5) / 64.0)
        A2 = (15.0 / 16) * (n**2 - (n**4) / 4.0)
        A3 = -(35.0 / 48) * (n**3 - (5.0 / 16) * (n**5))
        A4 = (315.0 / 512) * (n**4)
        A5 = -(693.0 / 1280) * (n**5)
        return np.array([A0, A1, A2, A3, A4, A5])

    def alpha_array(n):
        a0 = np.nan  # dummy
        a1 = (
            (1.0 / 2) * n
            - (2.0 / 3) * (n**2)
            + (5.0 / 16) * (n**3)
            + (41.0 / 180) * (n**4)
            - (127.0 / 288) * (n**5)
        )
        a2 = (
            (13.0 / 48) * (n**2)
            - (3.0 / 5) * (n**3)
            + (557.0 / 1440) * (n**4)
            + (281.0 / 630) * (n**5)
        )
        a3 = (61.0 / 240) * (n**3) - (103.0 / 140) * (n**4) + (15061.0 / 26880) * (n**5)
        a4 = (49561.0 / 161280) * (n**4) - (179.0 / 168) * (n**5)
        a5 = (34729.0 / 80640) * (n**5)
        return np.array([a0, a1, a2, a3, a4, a5])

    # 定数 (a, F: 世界測地系-測地基準系1980（GRS80）楕円体)
    m0 = 0.9999
    a = 6378137.0
    F = 298.257222101

    # (1) n, A_i, alpha_iの計算
    n = 1.0 / (2 * F - 1)
    A_array = A_array(n)
    alpha_array = alpha_array(n)

    # (2), S, Aの計算
    A_ = ((m0 * a) / (1.0 + n)) * A_array[0]  # [m]
    S_ = ((m0 * a) / (1.0 + n)) * (
        A_array[0] * phi0_rad
        + np.dot(A_array[1:], np.sin(2 * phi0_rad * np.arange(1, 6)))
    )  # [m]

    # (3) lambda_c, lambda_sの計算
    lambda_c = np.cos(lambda_rad - lambda0_rad)
    lambda_s = np.sin(lambda_rad - lambda0_rad)

    # (4) t, t_の計算
    t = np.sinh(
        np.arctanh(np.sin(phi_rad))
        - ((2 * np.sqrt(n)) / (1 + n))
        * np.arctanh(((2 * np.sqrt(n)) / (1 + n)) * np.sin(phi_rad))
    )
    t_ = np.sqrt(1 + t * t)

    # (5) xi', eta'の計算
    xi2 = np.arctan(t / lambda_c)  # [rad]
    eta2 = np.arctanh(lambda_s / t_)

    # (6) x, yの計算
    x = (
        A_
        * (
            xi2
            + np.sum(
                np.multiply(
                    alpha_array[1:],
                    np.multiply(
                        np.sin(2 * xi2 * np.arange(1, 6)),
                        np.cosh(2 * eta2 * np.arange(1, 6)),
                    ),
                )
            )
        )
        - S_
    )  # [m]
    y = A_ * (
        eta2
        + np.sum(
            np.multiply(
                alpha_array[1:],
                np.multiply(
                    np.cos(2 * xi2 * np.arange(1, 6)),
                    np.sinh(2 * eta2 * np.arange(1, 6)),
                ),
            )
        )
    )  # [m]
    # return
    return x, y  # [m]


# x, y = calc_xy(36.103774791666666, 140.08785504166664, 36., 139+50./60)
# print("x, y = ({0}, {1})".format(x, y))
# <<実行結果>>
# x, y = (11543.6883215, 22916.2435543)

if __name__ == "__main__":
    # 平面直角座標系の原点 (36°, 139°50′)
    phi0_deg = 36.0
    lambda0_deg = 139 + 50 / 60

    # クラスターファイル処理
    for i in range(1, 11):
        df = pd.read_csv(f"../output/cluster{i:02d}.csv")
        xy_coords = [
            calc_xy(row["latitude"], row["longitude"], phi0_deg, lambda0_deg)
            for _, row in df.iterrows()
        ]
        df["x"] = [coord[0] for coord in xy_coords]
        df["y"] = [coord[1] for coord in xy_coords]
        df.to_csv(f"../output/cluster{i:02d}.csv", index=False)

    # 重心ファイル処理
    df = pd.read_csv("../output/centers.csv")
    xy_coords = [
        calc_xy(row["latitude"], row["longitude"], phi0_deg, lambda0_deg)
        for _, row in df.iterrows()
    ]
    df["x"] = [coord[0] for coord in xy_coords]
    df["y"] = [coord[1] for coord in xy_coords]
    df.to_csv(f"../output/centers.csv", index=False)
