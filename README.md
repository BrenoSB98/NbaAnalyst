# NbaAnalytics

Plataforma web de análise estatística da NBA desenvolvida como Trabalho de Conclusão de Curso (TCC) para o curso de **Sistemas de Informação**. O objetivo é tornar dados complexos da NBA acessíveis para **apostadores casuais e amadores**, transformando estatísticas brutas em palpites, gráficos e análises visuais de fácil interpretação.

---

## Contextualização

O mercado de apostas esportivas cresceu significativamente no Brasil após a regulamentação das bets, mas a grande maioria dos apostadores ainda toma decisões com base em intuição, sem acesso a dados estruturados. Este projeto propõe uma alternativa: uma plataforma que coleta dados oficiais da NBA via API externa, processa essas informações em um pipeline automatizado e as disponibiliza em uma interface simples, com palpites gerados por um modelo preditivo de machine learning e um assistente conversacional especializado no esporte.

---

## Arquitetura

O projeto é composto por cinco camadas principais:

**Backend (FastAPI)** expõe uma API REST que serve os dados ao frontend, gerencia autenticação de usuários via JWT, processa as requisições ao modelo preditivo e se comunica com o assistente de IA. Toda a lógica de negócio está organizada em routers, services e schemas.

**Banco de Dados (PostgreSQL)** armazena jogos, times, jogadores, estatísticas por partida, temporadas, palpites gerados e usuários. As migrações são gerenciadas pelo Alembic. O pgAdmin está disponível para inspeção visual do banco.

**Pipeline de Dados (Apache Airflow)** orquestra três DAGs: carga diária incremental (partidas e estatísticas do dia anterior), backfill histórico e retreinamento semanal dos modelos preditivos. Os dados brutos são consumidos da API-Sports (NBA v2).

**Inteligência Artificial** divide-se em dois componentes: o **Onerb IA**, um chatbot especializado em NBA construído com LangChain e GPT-4o Mini que responde perguntas em linguagem natural consultando diretamente o banco de dados; e o **Modelo Preditivo**, treinado com XGBoost a partir de estatísticas históricas de jogadores para estimar pontos, assistências, rebotes, roubos e bloqueios nos jogos do dia.

**Frontend (HTML/JS/Bootstrap 5)** é uma aplicação multi-página servida por Nginx, com gráficos interativos em D3.js, autenticação baseada em token e layout responsivo.

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

| Camada | Tecnologias |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic, Pydantic |
| Banco de Dados | PostgreSQL 15, pgAdmin 4 |
| Pipeline ETL | Apache Airflow, API-Sports (NBA v2) |
| Machine Learning | XGBoost, scikit-learn, NumPy |
| IA Conversacional | LangChain, GPT-4o Mini (OpenAI), ChromaDB |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, D3.js |
| Infraestrutura | Docker, Docker Compose, Nginx |

---

## Como Utilizar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/) instalados
- Chave de acesso à [API-Sports](https://api-sports.io/) (plano NBA v2)
- Chave de API da [OpenAI](https://platform.openai.com/api-keys)

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

Abra o arquivo `.env` e preencha os campos obrigatórios:

```env
# Temporada NBA
NBA_SEASON=2025

# Banco de Dados
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=nba_score_db

# pgAdmin
PGADMIN_EMAIL=seu@email.com
PGADMIN_PASSWORD=sua_senha_pgadmin

# API-Sports (fonte dos dados NBA)
API_SPORTS_KEY=sua_chave_api_sports

# OpenAI (chatbot Onerb IA)
OPENAI_API_KEY=sua_chave_openai

# Segurança JWT
SECRET_KEY=uma_string_secreta_longa_e_aleatoria

# Airflow
AIRFLOW__CORE__FERNET_KEY=sua_fernet_key
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=sua_senha_airflow
AIRFLOW_ADMIN_EMAIL=seu@email.com
AIRFLOW_DB_USER=seu_usuario
AIRFLOW_DB_PASSWORD=sua_senha
AIRFLOW_DB_NAME=airflow_db
```

> **Dica:** para gerar uma `FERNET_KEY` válida para o Airflow, execute `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

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

1. `nba_backfill_historico` — carga histórica de jogos e estatísticas (executar uma vez)
2. `nba_carga_diaria_incremental` — passa a rodar automaticamente todo dia às 9h

### 6. Acessar a plataforma

| Serviço | Endereço |
|---|---|
| **Frontend (plataforma)** | http://localhost:3000 |
| **Backend (API)** | http://localhost:8000 |
| **Documentação da API** | http://localhost:8000/docs |
| **Apache Airflow** | http://localhost:8080 |
| **pgAdmin** | http://localhost:5050 |

---

## Estrutura do Projeto

```
NbaAnalytics/
├── airflow/                    # DAGs e configuração do Airflow
│   └── dags/
│       ├── nba_daily_incremental_dag.py
│       ├── nba_historical_backfill_dag.py
│       └── nba_retreinamento_semanal_dag.py
├── backend/
│   └── app/
│       ├── db/                 # Models, sessão e utilitários do banco
│       ├── etl/                # Scripts de carga e normalização de dados
│       ├── routers/            # Endpoints da API REST
│       ├── schemas/            # Validação de entrada/saída (Pydantic)
│       └── services/           # Lógica de negócio e ML
├── chat/                       # Módulo do chatbot Onerb IA (LangChain)
├── frontend/
│   ├── css/                    # Estilos por página
│   ├── js/                     # Scripts de autenticação e componentes
│   └── *.html                  # Páginas da aplicação
└── docker-compose.yml
```

---

## Contato

Desenvolvido por **Breno Braido** como TCC do curso de Sistemas de Informação.

<a href="https://www.linkedin.com/in/bbraido2/" target="_blank">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linkedin/linkedin-original.svg" width="32" />
</a>
&nbsp;
<a href="https://github.com/BrenoSB98" target="_blank">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/github/github-original.svg" width="32" />
</a>
&nbsp;
📧 **brenosilvabraido1998@gmail.com**

---

<div align="center">
  <sub>Desenvolvido como Trabalho de Conclusão de Curso — Sistemas de Informação</sub>
</div>