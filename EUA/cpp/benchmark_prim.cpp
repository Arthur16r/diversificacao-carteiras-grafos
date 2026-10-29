// Reutiliza literalmente o Prim do projeto, sem duplicar sua implementação.
#define PRIM_SEM_MAIN
#include "mst.cpp"

#include <chrono>
#include <cstdint>
#include <filesystem>
#include <iomanip>
#include <random>
#include <stdexcept>

using Relogio = std::chrono::steady_clock;
volatile double consumidor = 0.0;

Grafo gerarGrafo(int n, unsigned seed) {
    Grafo g;
    g.nomes.resize(n);
    g.dist.assign(n, std::vector<double>(n, 0.0));
    std::mt19937 rng(seed);
    // Conversão explícita reproduzível, sem depender de uniform_real_distribution.
    for (int i = 0; i < n; ++i) {
        g.nomes[i] = std::to_string(i);
        for (int j = i + 1; j < n; ++j) {
            double peso = 0.1 + 1.9 * (static_cast<double>(rng()) / 4294967296.0);
            g.dist[i][j] = g.dist[j][i] = peso;
        }
    }
    return g;
}

double medirLote(const Grafo& g, int chamadas) {
    const auto inicio = Relogio::now();
    for (int i = 0; i < chamadas; ++i) {
        auto arvore = primMST(g); // Inclui alocações e destruição dos vetores.
        // Consumo O(1) impede eliminação do resultado pelo otimizador.
        consumidor = consumidor + arvore.back().peso + arvore.size();
    }
    return std::chrono::duration<double, std::nano>(Relogio::now() - inicio).count();
}

void executar(const Grafo& g, const std::string& origem, unsigned seed, std::ofstream& csv) {
    auto verificacao = primMST(g);
    if (g.n() < 2 || verificacao.size() != static_cast<std::size_t>(g.n() - 1))
        throw std::runtime_error("Entrada nao gerou V-1 arestas");
    // Aquecimento e calibração não entram nas amostras registradas.
    medirLote(g, 2);
    int chamadas = 1;
    while (medirLote(g, chamadas) < 20000000.0 && chamadas < 65536)
        chamadas *= 2;
    for (int repeticao = 0; repeticao < 10; ++repeticao) {
        const double ns = medirLote(g, chamadas);
        const std::uint64_t v = g.n();
        csv << origem << ',' << v << ',' << seed << ',' << repeticao << ','
            << chamadas << ',' << ns / chamadas << ',' << v * (v - 1) / 2 << ','
            << 2 * v * v << ',' << v * v * sizeof(double) << '\n';
    }
    csv.flush();
    std::cerr << origem << " V=" << g.n() << " seed=" << seed << " concluido\n";
}

int main(int argc, char** argv) {
    if (argc != 3 && !(argc == 4 && std::string(argv[3]) == "--grandes")) {
        std::cerr << "Uso: benchmark_prim diretorio_saida matriz_real.csv [--grandes]\n";
        return 1;
    }
    try {
        std::filesystem::path pasta(argv[1]);
        std::filesystem::create_directories(pasta);
        std::ofstream csv(pasta / "medicoes.csv");
        if (!csv) throw std::runtime_error("Nao foi possivel abrir medicoes.csv");
        csv << std::setprecision(17);
        csv << "origem,vertices,seed,repeticao,chamadas_lote,tempo_ns,arestas,"
               "visitas_teoricas_lacos,bytes_matriz_dados\n";
        std::ofstream ambiente(pasta / "compilacao.txt");
        ambiente << "Compilador: " << __VERSION__ << "\nC++: " << __cplusplus
                 << "\nFlags previstas pelo Makefile: -std=c++17 -Wall -O2"
                 << "\nsteady_clock::is_steady: " << Relogio::is_steady
                 << "\nPeriodo nominal do relogio: " << Relogio::period::num << '/'
                 << Relogio::period::den << " segundos\n";
        const bool grandes = argc == 4;
        if (!grandes) executar(lerMatrizDistancia(argv[2]), "real", 0, csv);
        const std::vector<int> tamanhos = grandes ? std::vector<int>{10000, 20000}
            : std::vector<int>{50, 100, 200, 400, 800, 1600, 3200};
        for (int n : tamanhos)
            for (unsigned seed : {42u, 43u, 44u, 45u, 46u})
                executar(gerarGrafo(n, seed), "sintetico", seed, csv);
    } catch (const std::exception& e) {
        std::cerr << "Erro: " << e.what() << '\n';
        return 1;
    }
    return 0;
}
