# NbaAnalytics

Plataforma de análise de dados da NBA desenvolvida como Trabalho de Conclusão de Curso (TCC) para o curso de **Sistemas de Informação**. O sistema transforma estatísticas brutas em visualizações, comparativos e previsões acessíveis, oferecendo uma experiência completa de exploração de dados do basquete profissional.

---

## Contextualização

A NBA gera um volume massivo de dados a cada temporada, sendo pontuações, eficiência, desempenho por jogador, tendências por equipe, padrões de confronto, evolução ao longo dos jogos. A maior parte dessas informações está espalhada em fontes técnicas voltadas para profissionais, com pouca acessibilidade para fãs casuais e estudantes da modalidade.

Este projeto integra coleta automatizada de dados oficiais, modelos preditivos de machine learning e um assistente conversacional especializado em uma única plataforma. O usuário tem em um só lugar: estatísticas completas de times e jogadores, classificação por temporada, comparativos de confronto, previsões de desempenho dos próximos jogos e um chatbot capaz de responder perguntas sobre regras, história, táticas e fatos atuais da liga.

---

## Arquitetura

O projeto é composto por cinco camadas principais:

**Backend (FastAPI)** expõe uma API REST que serve os dados ao frontend, gerencia autenticação de usuários via JWT, processa as requisições ao modelo preditivo e se comunica com o assistente de IA. A lógica de negócio está organizada em routers, services e schemas. Inclui também recuperação de senha por e-mail via SMTP e painel administrativo.

**Banco de Dados (PostgreSQL)** armazena jogos, times, jogadores, estatísticas por partida, temporadas, previsões geradas, predições retroativas e usuários. As migrações são gerenciadas pelo Alembic. O pgAdmin está disponível para inspeção visual do banco.

**Pipeline de Dados (Apache Airflow)** orquestra cinco DAGs: carga diária incremental, backfill histórico completo, DAG específica de playoffs, retreinamento dos modelos preditivos e cálculo de predições retroativas para validação da acurácia. Os dados brutos são consumidos da API-Sports (NBA v2).

**Inteligência Artificial** divide-se em dois componentes:

- **Onerb IA**: chatbot especializado em NBA construído com LangChain e o modelo **Llama 3.3 70B Versatile** hospedado no **Groq Cloud**. O chatbot usa _tool calling_ autônomo para escolher entre sete ferramentas que consultam o banco de dados, uma base de conhecimento local com 34 documentos sobre regras/táticas/história e busca web em tempo real via **Tavily**.
- **Modelo Preditivo**: treinado com XGBoost a partir de estatísticas históricas de jogadores para estimar pontos, assistências, rebotes, roubos e bloqueios nos jogos do dia.

**Frontend (HTML/JS/Bootstrap 5)** é uma aplicação multi-página servida por Nginx, com gráficos interativos em D3.js, autenticação baseada em token JWT e layout responsivo.

---

## Funcionalidades do Onerb IA

O chatbot tem acesso a sete ferramentas que ele escolhe autonomamente conforme a pergunta:

| Ferramenta                | Quando é usada                                              |
| ------------------------- | ----------------------------------------------------------- |
| `stats_jogador_temporada` | Médias de um jogador em uma temporada                       |
| `jogos_time`              | Resultados de um time por mês ou temporada                  |
| `lideres_liga`            | Top N em pontos, assistências, rebotes, roubos ou tocos     |
| `comparar_jogadores`      | Comparativo lado a lado entre 2 a 5 jogadores               |
| `classificacao_temporada` | Standings de uma temporada                                  |
| `buscar_conhecimento_nba` | Regras, posições, táticas, analytics, história, dinastias   |
| `buscar_web`              | MVP, campeão, lesões, trades, jogos de hoje, fatos recentes |

O assistente segue uma hierarquia de fontes: estatísticas e jogos vão para o banco; conceitos e regras vão para a base de conhecimento; fatos atuais e novidades vão para a web. Se o banco retornar dados desatualizados ou vazios, a busca web é acionada como complemento.

A cada conversa, o chatbot mantém o histórico completo do diálogo limitado a 30k tokens por requisição (com truncagem automática das mensagens mais antigas) e 200k tokens acumulados por sessão. O histórico é client-side e é zerado ao recarregar a página ou ao deslogar.

---

## Tecnologias Utilizadas

<div align="center">

<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/python/python-original.svg" width="48" title="Python" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/fastapi/fastapi-original.svg" width="48" title="FastAPI" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/postgresql/postgresql-original.svg" width="48" title="PostgreSQL" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/docker/docker-original.svg" width="48" title="Docker" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/apacheairflow/apacheairflow-original.svg" width="48" title="Apache Airflow" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/javascript/javascript-original.svg" width="48" title="JavaScript" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/html5/html5-original.svg" width="48" title="HTML5" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/css3/css3-original.svg" width="48" title="CSS3" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/bootstrap/bootstrap-original.svg" width="48" title="Bootstrap" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/d3js/d3js-original.svg" width="48" title="D3.js" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/nginx/nginx-original.svg" width="48" title="Nginx" />
&nbsp;&nbsp;
<img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/git/git-original.svg" width="48" title="Git" />

</div>

| Camada            | Tecnologias                                                                                 |
| ----------------- | ------------------------------------------------------------------------------------------- |
| Backend           | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic, JWT                                  |
| Banco de Dados    | PostgreSQL 15, pgAdmin 4                                                                    |
| Pipeline ETL      | Apache Airflow, API-Sports (NBA v2)                                                         |
| Machine Learning  | XGBoost, scikit-learn, NumPy                                                                |
| IA Conversacional | LangChain, Groq Cloud (Llama 3.3 70B Versatile), Tavily Search, retriever por palavra-chave |
| Frontend          | HTML5, CSS3, JavaScript, Bootstrap 5, D3.js                                                 |
| Infraestrutura    | Docker, Docker Compose, Nginx                                                               |
| E-mail            | SMTP (recuperação de senha, confirmação de conta)                                           |

---

## Como Utilizar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/) instalados
- Chave de acesso à [API-Sports](https://api-sports.io/) (plano NBA v2)
- Chave de API do [Groq Cloud](https://console.groq.com/) (plano gratuito disponível)
- Chave de API do [Tavily Search](https://app.tavily.com/) (plano gratuito disponível)
- Credenciais SMTP para envio de e-mails (Gmail com senha de app, por exemplo)

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/NbaAnalyst.git
cd NbaAnalyst
```

### 2. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Os campos essenciais a preencher no `.env` são as credenciais do banco de dados, as chaves de API (API-Sports, Groq, Tavily), as credenciais SMTP para envio de e-mails e os segredos JWT/Airflow.

> **Dicas para configurar as chaves:**
>
> - **Groq**: cadastre-se em [console.groq.com](https://console.groq.com) e gere uma API key gratuita. O plano gratuito tem limite diário de 100.000 tokens, suficiente para uso pessoal e desenvolvimento.
> - **Tavily**: cadastre-se em [app.tavily.com](https://app.tavily.com) e gere uma API key. O plano gratuito oferece 1.000 buscas/mês.
> - **FERNET_KEY do Airflow**: gere com `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
> - **SMTP do Gmail**: use uma [senha de aplicativo](https://support.google.com/accounts/answer/185833) em vez da senha pessoal.

### 3. Subir a aplicação

```bash
docker compose up -d --build
```

O primeiro build pode demorar alguns minutos, pois instala todas as dependências dos containers.

### 4. Executar as migrações do banco

Após os containers subirem:

```bash
docker compose exec backend alembic upgrade head
```

### 5. Carregar os dados iniciais

Acesse o Airflow em `http://localhost:8080`, faça login com as credenciais definidas no `.env` e ative as DAGs na seguinte ordem:

1. `nba_historical_backfill_dag` — carga histórica de jogos e estatísticas (executar uma vez)
2. `nba_daily_incremental_dag` — passa a rodar automaticamente todo dia
3. `nba_playoffs_dag` — carga específica dos jogos de playoff
4. `nba_retreinamento_dag` — retreina os modelos preditivos periodicamente
5. `nba_predicoes_retroativas_dag` — calcula predições retroativas para validar acurácia

### 6. Acessar a plataforma

| Serviço                   | Endereço                     |
| ------------------------- | ---------------------------- |
| **Frontend (plataforma)** | <http://localhost:3000>      |
| **Backend (API)**         | <http://localhost:8000>      |
| **Documentação da API**   | <http://localhost:8000/docs> |
| **Apache Airflow**        | <http://localhost:8080>      |
| **pgAdmin**               | <http://localhost:5050>      |

---

## Estrutura do Projeto

```
NbaAnalytics/
├── airflow/
│   └── dags/
│       ├── nba_daily_incremental_dag.py       # Carga diária incremental
│       ├── nba_historical_backfill_dag.py     # Backfill histórico completo
│       ├── nba_playoffs_dag.py                # Carga específica de playoffs
│       ├── nba_predicoes_retroativas_dag.py   # Predições retroativas (acurácia)
│       └── nba_retreinamento_dag.py           # Retreinamento dos modelos ML
├── backend/
│   ├── alembic/                               # Migrations do banco
│   └── app/
│       ├── db/                                # Models SQLAlchemy e sessão
│       ├── etl/                               # Scripts de carga e normalização
│       ├── routers/                           # Endpoints da API REST
│       │   ├── admin.py        analytics.py   api.py       auth.py
│       │   ├── chat.py         confronto.py   game.py      league.py
│       │   ├── player.py       predictions.py season.py    team.py
│       │   └── win_rate.py
│       ├── schemas/                           # Validação Pydantic
│       └── services/                          # Lógica de negócio e ML
├── chat/                                      # Módulo do Onerb IA
│   ├── oraculo.py                             # Pipeline principal + tool calling
│   ├── db_chat.py                             # 5 ferramentas tipadas do banco
│   ├── base.py                                # Retriever por palavra-chave
│   ├── conhecimento_nba.py                    # 34 documentos estáticos
│   ├── web_search.py                          # Busca web (Tavily) + query enrichment
│   ├── prompts.py                             # System prompt e descrições das tools
│   └── requirements.txt
├── frontend/
│   ├── css/                                   # Estilos por página
│   ├── img/                                   # Imagens estáticas
│   ├── js/                                    # Scripts de autenticação e componentes
│   └── *.html                                 # 17 páginas (login, cadastro, predições,
│                                              # estatísticas, classificação, times,
│                                              # jogador, perfil, chatbot Onerb etc)
├── nginx/                                     # Configuração do servidor web
├── test/                                      # Testes
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## Contato

Desenvolvido por **Breno Braido** como TCC do curso de Sistemas de Informação.

<div>
  <a href="https://github.com/BrenoSB98" target="_blank"> <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg" width="32" /> </a> &nbsp;
  <a href = "mailto:brenosilvabraido1998@gmail.com"><img src="https://img.shields.io/badge/-Gmail-%23333?style=for-the-badge&logo=gmail&logoColor=white" target="_blank"></a>
  <a href="https://instagram.com/bbraido2" target="_blank"><img src="https://img.shields.io/badge/-Instagram-%23E4405F?style=for-the-badge&logo=instagram&logoColor=white" target="_blank"></a>
  <a href="https://www.linkedin.com/in/bbraido2" target="_blank"><img src="https://img.shields.io/badge/-LinkedIn-%230077B5?style=for-the-badge&logo=linkedin&logoColor=white" target="_blank"></a>
</div>

---

<div align="center">
  <sub>Desenvolvido como Trabalho de Conclusão de Curso para o curso de Sistemas de Informação</sub>
</div>
