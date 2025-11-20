# Processador de mídia

O **Processador de mídia** é uma ferramenta para processamento de mídia local. Ele unifica extração de frames de vídeo, compressão de imagens, renomeação sequencial e criação de GIFs em um único fluxo de trabalho contínuo.

---

## 📖 Guia Prático (Como Utilizar)

Este software funciona em pipeline. Você insere um arquivo ou pasta no início, configura as etapas desejadas, e ele entrega o resultado final processado.

### 1. Configuração Inicial
* **Fonte:** Escolha entre **Vídeo** (para extrair frames) ou **Pasta** (para processar imagens já existentes).
* **Destino:** Escolha onde os arquivos finais serão salvos.

### 2. Módulos de Processamento
O programa ativa/desativa módulos automaticamente dependendo da sua fonte, mas você tem controle total:

#### 1️⃣ Extrator (Apenas para Vídeo)
* **Ativar Extração:** Obrigatório se a fonte for vídeo.
* **Intervalo (frames):** Define a cada quantos frames uma foto será tirada.
    * *Exemplo:* Se você coloca `5`, o software irá salvar 1 frame a cada 5 frames (1 gravado, 4 passados).

#### 2️⃣ Compressor/Redimensionador
Reduz o tamanho das imagens extraídas ou da pasta fonte.
* **Formato:** Escolha entre **JPEG**, **WEBP** (altamente recomendado para web) ou **PNG**.
* **Meta Tam. (%):** Define o tamanho do arquivo final desejado em relação ao original.
    * *Exemplo:* Se a imagem original tem 100KB e você define `80%`, o programa ajustará a qualidade para tentar atingir ~80KB.
    * *Nota:* Se escolher **PNG**, essa opção é desativada pois PNG é *Lossless* (sem perda), sendo mais voltada para redimensionar as imagens.
* **Resolução:**
    * **Presets:** Escolha resoluções padrão (4K, Full HD, HD).
    * **Original:** Mantém o tamanho nativo.
    * **Customizado:** Defina Largura e Altura manualmente.

#### 3️⃣ Renomeador
Organiza a bagunça de arquivos.
* **Prefixo:** Define o nome base dos arquivos.
    * *Resultado:* `prefixo_0.jpg`, `prefixo_1.jpg`, etc.

#### 4️⃣ GIF Maker
Cria uma animação com todas as imagens processadas.
* **ms:** Duração de cada frame em milissegundos (ex: 67ms ≈ 15 FPS / 33ms ≈ 30 FPS / 16ms ≈ 60 FPS).
* **Nome:** O nome do arquivo GIF final.

### 3. Execução e Monitoramento
Clique em **🚀 INICIAR PROCESSAMENTO**.
* Acompanhe a **Barra de Progresso** global.
* Verifique o **Log Detalhado** para ver o tamanho de cada arquivo antes e depois da compressão.
* Observe o **ETA (Tempo Estimado)** para saber quanto falta para terminar.

---

## ⚙️ Documentação Técnica (Como Funciona)

Este projeto foi construído em **Python 3.12+** utilizando uma arquitetura orientada a eventos com processamento multithread para garantir que a interface nunca trave, mesmo processando milhares de arquivos.

### Tecnologias Utilizadas
* **Interface Gráfica:** `ttkbootstrap` (wrapper moderno sobre o `tkinter` padrão) com tema *Darkly*.
* **Manipulação de Vídeo:** `OpenCV (cv2)` para leitura de streams de vídeo e contagem de frames.
* **Processamento de Imagem:** `Pillow (PIL)` para redimensionamento (LANCZOS), conversão de canais de cor e compressão.
* **Concorrência:** `threading` nativo do Python.

### Estrutura do Código

#### 1. A Classe `AppPipelineMonocromatica`
O código é encapsulado em uma classe monolítica que gerencia o estado da aplicação.
* **UI Construction (`_criar_*`):** Métodos dedicados a desenhar cada seção da tela.
* **State Management:** Variáveis `BooleanVar` e `StringVar` controlam o estado dos *widgets* e regras de negócio (ex: bloquear extrator se a fonte for pasta).

#### 2. Algoritmo de Compressão Inteligente (`encontrar_qualidade`)
Diferente de compressores comuns que usam uma qualidade fixa, este software implementa uma **Busca Binária (Binary Search)** em memória RAM.
1.  Ele define um intervalo de qualidade (1 a 100).
2.  Salva a imagem em um *buffer* de memória (`io.BytesIO`).
3.  Verifica se o tamanho em bytes atende à meta percentual.
4.  Ajusta a qualidade para cima ou para baixo até encontrar o melhor equilíbrio entre qualidade visual e tamanho de arquivo alvo.

#### 3. A Pipeline de Execução (`run_pipeline`)
O método principal roda em uma Thread separada e segue um fluxo linear estrito:

1.  **Fase 1 (Aquisição):**
    * *Se Vídeo:* Itera sobre o objeto `cv2.VideoCapture`. Extrai frames baseados no módulo da divisão (`count % interval == 0`).
    * *Se Pasta:* Itera sobre `os.listdir`.
    * *Processamento:* Aplica redimensionamento e compressão imediatamente (na memória) antes de escrever no disco, economizando I/O.
2.  **Fase 2 (Ordenação):**
    * Utiliza ordenação natural (`natural_sort_key`) para garantir que `frame_2` venha antes de `frame_10`.
    * Realiza renomeação em dois passos (temp -> final) para evitar conflitos de sobrescrita em sistemas de arquivos rápidos.
3.  **Fase 3 (GIF):**
    * Carrega todas as imagens processadas na memória RAM.
    * Utiliza a função `save` do Pillow com `append_images` e otimização delta para gerar o arquivo `.gif`.

### Logs e Telemetria
O sistema possui um método `update_status` que calcula a velocidade de processamento em tempo real:
$$\text{Rate} = \frac{\text{Itens Processados}}{\text{Tempo Decorrido}}$$
$$\text{ETA} = \frac{\text{Itens Restantes}}{\text{Rate}}$$
Isso fornece uma estimativa precisa de tempo restante para o usuário.

---

## 🚀 Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/media-pipeline-pro.git](https://github.com/seu-usuario/media-pipeline-pro.git)
    ```
2.  **Instale as dependências:**
    ```bash
    pip install ttkbootstrap opencv-python Pillow
    ```
3.  **Execute o programa:**
    ```bash
    python pipeline_pro.py
    ```

---

**Autor:** Hugo Borges + Gemini Pro 3