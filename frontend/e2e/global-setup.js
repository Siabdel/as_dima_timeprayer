/**
 * Setup global Playwright : purge les compteurs de throttle Redis avant la
 * suite E2E. En développement, le backend applique un throttle « register »
 * (5/h par IP) qui serait épuisé dès la 2e exécution des tests.
 *
 * Si Docker n'est pas disponible (ou sans stack en cours), l'étape est
 * ignorée silencieusement : les tests s'exécutent quand même.
 */
import { execSync } from 'node:child_process';

function purgeThrottleCounters() {
  try {
    // Vérifie que la stack Docker est en cours (service redis répond).
    execSync('docker compose exec -T redis redis-cli -n 0 ping', {
      cwd: '..',
      stdio: 'pipe',
      timeout: 10_000,
    });
    // Liste les clés de throttle puis les supprime.
    const keys = execSync(
      'docker compose exec -T redis redis-cli -n 0 --scan --pattern "*throttle*"',
      { cwd: '..', encoding: 'utf8', timeout: 10_000 }
    )
      .split('\n')
      .map((k) => k.trim())
      .filter(Boolean);
    if (keys.length) {
      execSync(
        `docker compose exec -T redis redis-cli -n 0 DEL ${keys.join(' ')}`,
        { cwd: '..', stdio: 'pipe', timeout: 10_000 }
      );
      console.log(`[e2e] ${keys.length} compteurs de throttle purgés.`);
    }
  } catch {
    console.log('[e2e] Redis indisponible — purge du throttle ignorée.');
  }
}

export default function globalSetup() {
  purgeThrottleCounters();
}
