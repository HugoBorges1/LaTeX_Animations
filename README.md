# Guia: Animações em LaTeX

Este documento apresenta o fluxo de trabalho definitivo para capturar, processar, incorporar animações em documentos LaTeX e armazená-las corretamente em repositórios digitais para garantir acessibilidade e preservação.

---

## 1. Captura e Criação dos Frames

O primeiro passo é obter a fonte visual da animação. Existem duas abordagens principais:

### A. Gravação de Tela
Utilize um software de captura para gravar a simulação ou vídeo desejado.
* **Recomendação:** [OBS Studio](https://obsproject.com/) (Open Broadcaster Software).
* **Motivo:** É gratuito, *open source*, leve e permite configurar diversos parâmetros da gravação (resolução, bitrate, framereate, dentre outros).

### B. Criação Manual
Gere os frames individualmente, manualmente, da forma que desejar.

---

## 2. Processamento de Mídia (ECRG)

Para preparar os arquivos para o LaTeX e para um repositório digital, utilize a ferramenta **ECRG** (Extrator, Compressor, Renomeador e GIFaker) incluída neste projeto (recomendado baixar o executável para utilizar, caso queira fazer alterações ou executar diretamente do código, o código fonte está em [ECRG fonte](https://github.com/HugoBorges1/LaTeX_Animations/blob/master/Extrator_Compressor_Renomeador_Gifmaker/ECRG.py)).

### Fluxo de Utilização:

1.  **Definição de Diretórios:**
    * **Fonte:** Selecione o arquivo de vídeo gravado ou a pasta contendo os frames brutos.
    * **Destino:** Crie ou selecione uma pasta vazia onde os arquivos processados serão salvos.

2.  **Configuração da Pipeline:**
    * **Extrator:** (Apenas para vídeo) Define o intervalo de captura. *Exemplo: se o valor for 5, o software irá salvar 1 frame a cada 5 quadros do vídeo.*
    * **Compressor:** Reduz o tamanho dos arquivos para evitar o estouro de tamanho do arquivo de TCC (75Mb). Recomenda-se o formato **JPEG** com o valor de qualidade ideal para cada situação.
    * **Ordenador:** Renomeia os arquivos sequencialmente (ex: `frame_0.jpg`, `frame_1.jpg`, ...) para que o LaTeX consiga lê-los em ordem.
    * **GIF Maker:** Gera um arquivo `.gif` único. Isso é essencial para exibir a animação em repositórios online (GitHub, Drive), já que o PDF so exibe as animações no software Adobe Acrobat.

3.  **Execução:**
    * Clique em **Iniciar Processamento**.
    * Aguarde o processo completar.
    * Verifique a pasta de destino.

---

## 3. Implementação no LaTeX

Para renderizar a animação dentro do PDF LaTeX, utiliza-se o pacote `animate`.

### 3.1. Preâmbulo
Adicione o pacote no início do seu arquivo `.tex` (antes do `\begin{document}`):

```latex
\usepackage{animate}    % Possibilita as animações
\usepackage{graphicx}   % Geralmente já utilizado
\usepackage{float}      % Para usar o modificador [H]
```

### 3.2. Inserindo os frames no código

```latex
\begin{figure}[H]
    \centering
    \animategraphics[loop, autoplay, width=1\textwidth]{W}{X}{Y}{Z}
    \caption{Legenda descritiva da animação.}
    \label{fig:label_da_animacao}
\end{figure}
```

A tabela abaixo mostra mais detalhes da sintaxe do comando "\animategraphics"

| Parâmetro | Descrição | Exemplo |
| :--- | :--- | :--- |
| **W** | **Frame Rate:** substitua pela quantidade de quadros por segundo. | `15` (15 imagens por segundo) |
| **X** | **Caminho + Prefixo:** substitua pelo caminho da pasta concatenado com o nome base dos arquivos (sem extensão e sem número). Perceba que o "scene" do exemplo se trata do prefixo do nome de TODOS os frames, por isso o software ECRG conta com um renomeador. | `figuras/animacao/scene` |
| **Y** | **Início:** substitua pelo número do sufixo do primeiro frame. | `0` |
| **Z** | **Fim:** substitua pelo número do sufixo do último frame. | `114` |

### Exemplo real:

Suponha que seus arquivos processados estejam na pasta frames_comprimidos, e os arquivos se chamem scene0.jpg até scene114.jpg.

```latex
\begin{figure}[H]
    \centering
    \animategraphics[loop, autoplay, width=0.85\textwidth]{15}{frames_comprimidos/scene}{0}{114}
    \caption{Cena do jogo representando o disparo da transição \textit{Learn deviant's name}.}
    \label{fig:animacao_jogo}
\end{figure}
```

## 4. Armazenamento e Acesso (Git LFS)

Se a intenção é incluir animações em uma monografia ou tese, não se pode depender apenas do PDF. O único software capaz de reproduzir essas animações corretamente é o **Adobe Acrobat Reader (Desktop)**. Leitores no navegador ou em celulares exibirão apenas uma imagem estática.

Para garantir o acesso universal, é necessário armazenar a animação (o GIF gerado pelo ECRG) em um repositório digital (GitHub, Google Drive, etc.).

Recomenda-se fortemente o **GitHub**. Como GIFs podem ser grandes (excedendo 100 MB), é necessário utilizar o **Git LFS (Large File Storage)**.

---

### Tutorial: GitHub + Git LFS no VS Code

Siga este passo a passo para criar um repositório e enviar seus arquivos pesados.

---

### Pré-requisitos

    1. Git instalado.
    2. Conta no GitHub.
    3. VS Code instalado.
    4. Extensão Git LFS instalada (comando: git lfs install).


---

### Passo 1: Criar o Repositório Remoto

1. Acesse **github.com/new**  
2. Configure o repositório e clique em **Create repository**  
3. Copie a URL (ex: `https://github.com/SeuUsuario/Repo.git`)

---

### Passo 2: Configurar o Repositório Local

Abra o terminal do VS Code na pasta onde estão seus arquivos/GIFs que você deseja armazenar no GitHub:

```bash
# 1. Iniciar o Git
git init

# 2. Renomear a branch principal para o padrão atual
git branch -m master main

# 3. Conectar ao repositório criado no GitHub
git remote add origin https://github.com/SeuUsuario/Repo.git

# Diz ao Git para tratar GIFs e vídeos via LFS
git lfs track "*.gif"

# Adiciona o arquivo de configuração gerado pelo LFS
git add .gitattributes
```

### Passo 3: Enviar os arquivos

```bash
# 1. Adicionar todos os arquivos ao stage
git add .

# 2. Criar o commit (salvar versão)
git commit -m "[Nome_desejado_para_o_commit]"

# 3. Enviar para o GitHub
git push -u origin main
```

Após o upload dos arquivos, é importante referenciar o repositório digital na monografia ou tese, garantindo que qualquer leitor possa acessar as animações e materiais complementares.

Você pode acessar o repósitório do meu TCC e entender como eu inseri minhas animações no arquivo de monografia e como eu referenciei elas no repositório: [Trabalho de consluão de curso](https://github.com/HugoBorges1/Trabalho_de_conclusao_de_curso)
