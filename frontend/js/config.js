var hostnameAtual = window.location.hostname;
var ehAmbienteDev = hostnameAtual === "localhost" || hostnameAtual === "127.0.0.1";

if (ehAmbienteDev) {
    window.API_BASE = "http://localhost:8000/api/v1";
} else {
    window.API_BASE = "https://api.nbaanalytics.com.br/api/v1";
}
 