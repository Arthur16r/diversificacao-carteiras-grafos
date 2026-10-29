// Le uma matriz de distancia (CSV) e extrai a Arvore Geradora Minima (MST)
// usando o algoritmo de Prim. Identico ao usado no projeto brasileiro --
// o algoritmo e agnostico de mercado, so os dados de entrada mudam.
//
// Uso: ./mst caminho/para/distance_matrix.csv

#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <vector>

struct Grafo {
    std::vector<std::string> nomes;
    std::vector<std::vector<double>> dist;
    int n() const { return static_cast<int>(nomes.size()); }
};

Grafo lerMatrizDistancia(const std::string& caminho) {
    std::ifstream arquivo(caminho);
    if (!arquivo.is_open()) {
        throw std::runtime_error("Nao consegui abrir o arquivo: " + caminho);
    }

    Grafo g;
    std::string linha;

    std::getline(arquivo, linha);
    // No Linux, getline remove LF, mas preserva CR de arquivos Windows (CRLF).
    if (!linha.empty() && linha.back() == '\r') linha.pop_back();
    std::stringstream cabecalho(linha);
    std::string celula;
    std::getline(cabecalho, celula, ',');
    while (std::getline(cabecalho, celula, ',')) {
        g.nomes.push_back(celula);
    }

    while (std::getline(arquivo, linha)) {
        if (!linha.empty() && linha.back() == '\r') linha.pop_back();
        if (linha.empty()) continue;
        std::stringstream ss(linha);
        std::getline(ss, celula, ',');

        std::vector<double> valores;
        while (std::getline(ss, celula, ',')) {
            valores.push_back(std::stod(celula));
        }
        g.dist.push_back(valores);
    }

    return g;
}

struct Aresta {
    int de;
    int para;
    double peso;
};

std::vector<Aresta> primMST(const Grafo& g) {
    int n = g.n();
    std::vector<bool> naArvore(n, false);
    std::vector<double> custoMinimo(n, std::numeric_limits<double>::max());
    std::vector<int> origem(n, -1);

    custoMinimo[0] = 0.0;
    std::vector<Aresta> resultado;

    for (int iter = 0; iter < n; ++iter) {
        int u = -1;
        double melhorCusto = std::numeric_limits<double>::max();
        for (int i = 0; i < n; ++i) {
            if (!naArvore[i] && custoMinimo[i] < melhorCusto) {
                melhorCusto = custoMinimo[i];
                u = i;
            }
        }
        if (u == -1) break;

        naArvore[u] = true;
        if (origem[u] != -1) {
            resultado.push_back({origem[u], u, custoMinimo[u]});
        }

        for (int v = 0; v < n; ++v) {
            if (!naArvore[v] && g.dist[u][v] < custoMinimo[v]) {
                custoMinimo[v] = g.dist[u][v];
                origem[v] = u;
            }
        }
    }

    return resultado;
}

#ifndef PRIM_SEM_MAIN
int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Uso: " << argv[0] << " caminho/para/distance_matrix.csv\n";
        return 1;
    }

    try {
        Grafo g = lerMatrizDistancia(argv[1]);
        std::cout << "Grafo carregado: " << g.n() << " ativos.\n\n";

        std::vector<Aresta> mst = primMST(g);

        double custoTotal = 0.0;
        std::cout << "Arestas da MST (ativo -- ativo : distancia)\n";
        std::cout << "--------------------------------------------\n";
        for (const auto& a : mst) {
            std::cout << g.nomes[a.de] << " -- " << g.nomes[a.para]
                      << " : " << a.peso << "\n";
            custoTotal += a.peso;
        }
        std::cout << "\nCusto total da MST: " << custoTotal << "\n";

        std::ofstream out("mst_edges.csv");
        out << "de,para,distancia\n";
        for (const auto& a : mst) {
            out << g.nomes[a.de] << "," << g.nomes[a.para] << "," << a.peso << "\n";
        }
        std::cout << "Arestas exportadas para mst_edges.csv\n";

    } catch (const std::exception& e) {
        std::cerr << "Erro: " << e.what() << "\n";
        return 1;
    }

    return 0;
}
#endif
