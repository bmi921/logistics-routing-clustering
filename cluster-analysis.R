# ライブラリ読み込み
library(foreign)   # DBFファイル読み込み
library(dplyr)     # データ操作
library(leaflet)   # OpenStreetMap用

# householdsデータ読み込み
households <- read.dbf("C:/Users/inyt1/Documents/sakai-exp/data/household5000.dbf", as.is = TRUE)

# 緯度・経度だけ抜き出し
coords <- households %>% select(longitude, latitude)

# K-meansクラスタリング（営業所10個想定）
set.seed(123)
kmeans_result <- kmeans(coords, centers = 9, nstart = 25)

# クラスタ番号を元データに追加
households$cluster <- kmeans_result$cluster

# セントロイドを取得
centroids <- as.data.frame(kmeans_result$centers)
centroids$cluster <- 1:nrow(centroids)  # セントロイドにクラスタ番号を追加

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
  addCircleMarkers(
    data = centroids, 
    ~longitude, ~latitude, 
    color = "black",  # セントロイドを黒色で表示
    radius = 8, fillOpacity = 1, stroke = TRUE, weight = 2
  ) %>%
  addLegend(
    "bottomright", pal = pal, 
    values = households$cluster, title = "Cluster", opacity = 1
  ) %>%
  setView(lng = mean(households$longitude), lat = mean(households$latitude), zoom = 10)
