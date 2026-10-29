// Le uma matriz de distancia (CSV) e extrai a Arvore Geradora Minima (MST)
// usando o algoritmo de Prim, adequado para grafos densos/completos como
// o nosso (todo ativo se conecta com todo ativo).
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
    std::vector<std::vector<double>> dist;  // matriz de adjacencia

    int n() const { return static_cast<int>(nomes.size()); }
};

// Le um CSV no formato: primeira linha = nomes dos ativos (com celula
// vazia no canto), linhas seguintes = nome do ativo + distancias.
Grafo lerMatrizDistancia(const std::string& caminho) {
    std::ifstream arquivo(caminho);
    if (!arquivo.is_open()) {
        throw std::runtime_error("Nao consegui abrir o arquivo: " + caminho);
    }

    Grafo g;
    std::string linha;

    // cabecalho
    std::getline(arquivo, linha);
    // No Linux, getline remove LF, mas preserva CR de arquivos Windows (CRLF).
    if (!linha.empty() && linha.back() == '\r') linha.pop_back();
    std::stringstream cabecalho(linha);
    std::string celula;
    std::getline(cabecalho, celula, ',');  // descarta canto vazio
    while (std::getline(cabecalho, celula, ',')) {
        g.nomes.push_back(celula);
    }

    // linhas de dados
    while (std::getline(arquivo, linha)) {
        if (!linha.empty() && linha.back() == '\r') linha.pop_back();
        if (linha.empty()) continue;
        std::stringstream ss(linha);
        std::getline(ss, celula, ',');  // nome da linha (ignorado, mesma ordem do cabecalho)

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

// Prim: comeca do no 0 e sempre adiciona a aresta mais barata que liga a
// arvore atual a um no ainda fora dela. Complexidade O(V^2), adequada
// para grafo denso (nao precisamos de heap para poucas dezenas de nos).
std::vector<Aresta> primMST(const Grafo& g) {
    int n = g.n();
    std::vector<bool> naArvore(n, false);
    std::vector<double> custoMinimo(n, std::numeric_limits<double>::max());
    std::vector<int> origem(n, -1);

    custoMinimo[0] = 0.0;
    std::vector<Aresta> resultado;

    for (int iter = 0; iter < n; ++iter) {
        // acha o no fora da arvore com menor custo de conexao
        int u = -1;
        double melhorCusto = std::numeric_limits<double>::max();
        for (int i = 0; i < n; ++i) {
            if (!naArvore[i] && custoMinimo[i] < melhorCusto) {
                melhorCusto = custoMinimo[i];
                u = i;
            }
        }
        if (u == -1) break;  // grafo desconexo (nao deve acontecer aqui)

        naArvore[u] = true;
        if (origem[u] != -1) {
            resultado.push_back({origem[u], u, custoMinimo[u]});
        }

        // atualiza custo de conexao dos vizinhos ainda fora da arvore
        for (int v = 0; v < n; ++v) {
            if (!naArvore[v] && g.dist[u][v] < custoMinimo[v]) {
                custoMinimo[v] = g.dist[u][v];
                origem[v] = u;
            }
        }
    }

    return resultado;
}

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

        // exporta pra CSV pra depois processar em Python (metrica de
        // diversificacao, backtest)
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
