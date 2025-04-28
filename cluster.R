# ライブラリ読み込み
library(foreign)   # DBFファイル読み込み
library(dplyr)     # データ操作
library(ggplot2)   # 可視化
library(leaflet)   # OpenStreetMap用

# householdsデータ読み込み
households <- read.dbf("C:/Users/inyt1/Documents/sakai-exp/data/household5000.dbf", as.is = TRUE)

# 緯度・経度だけ抜き出し
coords <- households %>% select(longitude, latitude)

# K-meansクラスタリング（営業所10個想定）
set.seed(123)
kmeans_result <- kmeans(coords, centers = 10, nstart = 25)

# クラスタ番号を元データに追加
households$cluster <- kmeans_result$cluster

# 色のパレットをクラスタごとに設定
pal <- colorFactor(palette = "Set1", domain = households$cluster)

# --- OpenStreetMapでプロット ---
leaflet(households) %>%
  addTiles() %>%  # OpenStreetMapタイルを追加
  addCircleMarkers(
    ~longitude, ~latitude, 
    color = ~pal(cluster),  # クラスタ番号で色分け
    radius = 5, fillOpacity = 0.7, stroke = FALSE
  ) %>%
  addLegend(
    "bottomright", pal = pal, 
    values = households$cluster, title = "Cluster", opacity = 1
  ) %>%
  setView(lng = mean(households$longitude), lat = mean(households$latitude), zoom = 10)
