# src/logic/segmentation.py

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import json
import os

class Segmentador:
    """
    Clase dedicada a realizar la segmentación y clustering de datos.
    """
    def __init__(self, n_clusters=5, random_state=42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state, n_init=10)

    def encontrar_k_optimo(self, df, metricas_seleccionadas, max_k=10):
        """
        Calcula la inercia para diferentes valores de k para encontrar el número óptimo
        de clusters usando el Método del Codo.
        """
        if not all(col in df.columns for col in metricas_seleccionadas):
            return pd.DataFrame()

        df_limpio = df.copy()
        df_limpio.dropna(subset=metricas_seleccionadas, inplace=True)
        if df_limpio.empty or len(df_limpio) < max_k:
            return pd.DataFrame()

        features = df_limpio[metricas_seleccionadas]
        features_scaled = self.scaler.fit_transform(features)

        inercias = []
        rango_k = range(2, max_k + 1)

        for k in rango_k:
            kmeans_temp = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans_temp.fit(features_scaled)
            inercias.append(kmeans_temp.inertia_)

        df_codo = pd.DataFrame({'k': rango_k, 'inercia': inercias})
        return df_codo

    def segmentar_dataframe(self, df, metricas_seleccionadas):
        """
        Realiza el clustering basándose en una lista dinámica de métricas.
        """
        if not all(col in df.columns for col in metricas_seleccionadas):
            return pd.DataFrame()

        df_limpio = df.copy()
        
        df_limpio.dropna(subset=metricas_seleccionadas, inplace=True)
        if df_limpio.empty or len(df_limpio) < self.n_clusters:
            return pd.DataFrame()

        features = df_limpio[metricas_seleccionadas]
        features_scaled = self.scaler.fit_transform(features)
        
        df_limpio['Cluster'] = self.kmeans.fit_predict(features_scaled)
        
        if len(metricas_seleccionadas) >= 2:
            pca = PCA(n_components=2)
            principal_components = pca.fit_transform(features_scaled)
            df_limpio['PC1'] = principal_components[:, 0]
            df_limpio['PC2'] = principal_components[:, 1]
        
        return df_limpio