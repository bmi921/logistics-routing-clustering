import numpy as np


def calc_lat_lon(x, y, phi0_deg, lambda0_deg):
    """平面直角座標を緯度経度に変換する
    - input:
        (x, y): 変換したいx, y座標[m]
        (phi0_deg, lambda0_deg): 平面直角座標系原点の緯度・経度[度]（分・秒でなく小数であることに注意）
    - output:
        latitude:  緯度[度]
        longitude: 経度[度]
        * 小数点以下は分・秒ではないことに注意
    """
    # 平面直角座標系原点をラジアンに直す
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

    def beta_array(n):
        b0 = np.nan  # dummy
        b1 = (
            (1.0 / 2) * n
            - (2.0 / 3) * (n**2)
            + (37.0 / 96) * (n**3)
            - (1.0 / 360) * (n**4)
            - (81.0 / 512) * (n**5)
        )
        b2 = (
            (1.0 / 48) * (n**2)
            + (1.0 / 15) * (n**3)
            - (437.0 / 1440) * (n**4)
            + (46.0 / 105) * (n**5)
        )
        b3 = (17.0 / 480) * (n**3) - (37.0 / 840) * (n**4) - (209.0 / 4480) * (n**5)
        b4 = (4397.0 / 161280) * (n**4) - (11.0 / 504) * (n**5)
        b5 = (4583.0 / 161280) * (n**5)
        return np.array([b0, b1, b2, b3, b4, b5])

    def delta_array(n):
        d0 = np.nan  # dummy
        d1 = (
            2.0 * n
            - (2.0 / 3) * (n**2)
            - 2.0 * (n**3)
            + (116.0 / 45) * (n**4)
            + (26.0 / 45) * (n**5)
            - (2854.0 / 675) * (n**6)
        )
        d2 = (
            (7.0 / 3) * (n**2)
            - (8.0 / 5) * (n**3)
            - (227.0 / 45) * (n**4)
            + (2704.0 / 315) * (n**5)
            + (2323.0 / 945) * (n**6)
        )
        d3 = (
            (56.0 / 15) * (n**3)
            - (136.0 / 35) * (n**4)
            - (1262.0 / 105) * (n**5)
            + (73814.0 / 2835) * (n**6)
        )
        d4 = (
            (4279.0 / 630) * (n**4)
            - (332.0 / 35) * (n**5)
            - (399572.0 / 14175) * (n**6)
        )
        d5 = (4174.0 / 315) * (n**5) - (144838.0 / 6237) * (n**6)
        d6 = (601676.0 / 22275) * (n**6)
        return np.array([d0, d1, d2, d3, d4, d5, d6])

    # 定数 (a, F: 世界測地系-測地基準系1980（GRS80）楕円体)
    m0 = 0.9999
    a = 6378137.0
    F = 298.257222101

    # (1) n, A_i, beta_i, delta_iの計算
    n = 1.0 / (2 * F - 1)
    A_array = A_array(n)
    beta_array = beta_array(n)
    delta_array = delta_array(n)

    # (2), S, Aの計算
    A_ = ((m0 * a) / (1.0 + n)) * A_array[0]
    S_ = ((m0 * a) / (1.0 + n)) * (
        A_array[0] * phi0_rad
        + np.dot(A_array[1:], np.sin(2 * phi0_rad * np.arange(1, 6)))
    )

    # (3) xi, etaの計算
    xi = (x + S_) / A_
    eta = y / A_

    # (4) xi', eta'の計算
    xi2 = xi - np.sum(
        np.multiply(
            beta_array[1:],
            np.multiply(
                np.sin(2 * xi * np.arange(1, 6)), np.cosh(2 * eta * np.arange(1, 6))
            ),
        )
    )
    eta2 = eta - np.sum(
        np.multiply(
            beta_array[1:],
            np.multiply(
                np.cos(2 * xi * np.arange(1, 6)), np.sinh(2 * eta * np.arange(1, 6))
            ),
        )
    )

    # (5) chiの計算
    chi = np.arcsin(np.sin(xi2) / np.cosh(eta2))  # [rad]
    latitude = chi + np.dot(delta_array[1:], np.sin(2 * chi * np.arange(1, 7)))  # [rad]

    # (6) 緯度(latitude), 経度(longitude)の計算
    longitude = lambda0_rad + np.arctan(np.sinh(eta2) / np.cos(xi2))  # [rad]

    # ラジアンを度になおしてreturn
    return np.rad2deg(latitude), np.rad2deg(longitude)  # [deg]
