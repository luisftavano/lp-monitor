// Dispara o workflow "LP monitor" no GitHub a cada 10 min (cron do wrangler.jsonc).
// Existe porque o agendamento do próprio GitHub Actions atrasa/pula execuções por horas.
// Não lê a blockchain nem guarda estado: só chama a API workflow_dispatch.

export default {
  async scheduled(controller, env) {
    const url = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${env.WORKFLOW_FILE}/dispatches`;
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "lp-monitor-scheduler",
      },
      body: JSON.stringify({ ref: "main", inputs: { modo: "normal" } }),
    });
    if (!resp.ok) {
      // Lança pra aparecer como erro nos logs do Worker (wrangler tail / painel).
      throw new Error(`GitHub respondeu ${resp.status}: ${(await resp.text()).slice(0, 300)}`);
    }
    console.log(`workflow disparado (${resp.status})`);
  },
};
