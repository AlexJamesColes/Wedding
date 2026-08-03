// The door. Guests give their name as it appears on the invitation;
// names are kept here only as salted fingerprints, never in the clear.
// Once admitted, a device stays admitted.
(function () {
  var KEY = 'ca-gate';
  try { if (localStorage.getItem(KEY) === '1') return; } catch (e) {}
  if (!(window.crypto && crypto.subtle && window.TextEncoder && window.Promise)) return;

  var SALT = 'C&A·MMXXVI·';
  var HASHES = {
  "00177737a4f16728168e8316807d4b377165a30716e3618eedbf1f4acc389098": 1, "0a5bfe991032d7f701a6cdf8f56fceae14faba558c480954d0152cc8b76beb4e": 1,
  "0f5197298e5af0d3b5dbe06db167b9a751f87837a03be860bafdcb28c37a7264": 1, "198432b013121c86ea52578c62fb0025a50c0a9c057246a6c45b16b5a5bad600": 1,
  "1a3c030c1ee2a3b29f59136f7ebddddeb6e962313df22feabe39f223c440a65a": 1, "1ab1a1c4f463125b6789bd4b93a2cab56f1a31d7a4c11fa841e9de948fef6359": 1,
  "1ad1fd2f2bb3139b73934f0e52040b3d5b3bdc7c254b0cff6658c10e835fa10f": 1, "1c85f46097d6eb35f4ee34b6bac450da6b78c33d591c658a7dca667e520a99e4": 1,
  "2b2059c092dae92148dfa7c3a72438b8d2c69ed8944e0d5373b39a97d807b8fd": 1, "35dfa4b6ed3ce027c3d6b7d31146dfa47ee47bd8ad6d52442430c61574b159f0": 1,
  "3c76b5a579c938911d0ad9f5bf233715b52737857761be23241ec564fb226aa5": 1, "469c0fcc508299287b57fbe927b904c8690feaaa9e29a151ed69b7db5d0557ff": 1,
  "49322246c562190b5cc6d0c622861a91a103198fb2c71edd4b36a86d588a270c": 1, "4fc64138e433a8af038de138c0f7768f7f0bb670cf6ac95d65ba74e7f5615cb2": 1,
  "55ad794064c897895eb14e4789dd7abaddbf14477e388177d2fd9d2560637a26": 1, "60ac3374464621de6a29ee50877a4126c2fe58b9417e87e0c07092cab9eadb37": 1,
  "6513d28ec277d61c7851cad5053bdccfa4217a6d330cc61f9e633f24995a3ac6": 1, "698c52baa772de9cd879f442af753ba37f362c87b56be5a8d3f50b69473d03bc": 1,
  "6cbcfc0c4058e8178a58f783dd2836dc87269c41629e4cf1fbe2cc3be5f38e57": 1, "7cb35af19ac1a44ef6d4e8705caf84768200672da3756aa71dd0f664de16e99c": 1,
  "7cc7b738a5ba688d4f507fe187518ccdc0a9a08c9e4f0f91523b6b8a6310503b": 1, "865144836bcadb0e1129720cf8a27c241a53b0fcab3c8bf323974a3b5cf9b5d5": 1,
  "8c1f0cbd3e15a46de0372163a46335a5b1e67c193c60bae58b0ae2e014fca222": 1, "90e76e29c10afe60d1073cfe557f8960c639480bc75cb138ff504493329b5550": 1,
  "9ba306af714fcd4593594d69233661d3bf0cf4d92ee73a276a6367baa2830208": 1, "a7a80ee2a0e69693f2494c1597b9a7c2fc816d7ec7ccab5a4d43a8658cf4816a": 1,
  "a940385c8e2d0f808dca440733197f45137885da811f0242f0dc83c5e8e5bb84": 1, "bcfd07462a94022dcf7500948292fd6233a59655f85e2519179f0c0da0462d45": 1,
  "c0860dbba5aea5fce9b5605cf3114471e4551faed69476cc219793ad85c798ef": 1, "c6c832a1223005d1961164f34b4788025258445fe3bdb486d2d8319fdcc4c480": 1,
  "d3fae43b6046d2a6b18f3cc3b7f3fa4860a436680464c99cf5ee26ec22b5f622": 1, "d5d553a89642f1995693aceac85d0474ca666684e7309114abfaf486e8e81392": 1,
  "e10b5f6e327229850d298290f7a58ba765816c28e155add92b541bdc740f36cd": 1, "e8e94143e8532a4eba5927fe73cfe4fde565756c4c78ed9938be97fe737fc751": 1,
  "e9413a663ff32d72777b954517d8ae45d6e27085bc13dfd9c24d7cc2a4037968": 1, "e96a958a3a981c7c3f598d6187dcfa6701774eea84d566831a3915f6a4eaec5b": 1,
  "efe89bb98e77d23eee48713db23725c16f41d0305b9fc67695ec62b6ed949841": 1, "f9d1769c6fb807cc06a5401591ee533a902d2f2a9a5b71b8cd82153c6688cb38": 1
  };

  document.documentElement.classList.add('gate-locked');
  var style = document.createElement('style');
  style.textContent =
    '.gate-locked { overflow: hidden; }' +
    '.gate-locked body > :not(.gate) { visibility: hidden; }' +
    '.gate { position: fixed; inset: 0; z-index: 999; background: #ece7d8; visibility: visible;' +
    '  display: flex; align-items: center; justify-content: center; text-align: center;' +
    '  opacity: 1; transition: opacity .7s ease; padding: 24px; }' +
    '.gate::before { content: ""; position: absolute; inset: 9px;' +
    '  border: 1px solid rgba(29,26,22,.13); pointer-events: none; }' +
    '.gate.gate-open { opacity: 0; pointer-events: none; }' +
    '.gate-inner { max-width: 420px; width: 100%; }' +
    '.gate-eyebrow { font-family: "Tenor Sans", sans-serif; font-size: 10px; letter-spacing: .34em;' +
    '  text-indent: .34em; text-transform: uppercase; color: #6e665a; margin: 30px 0 0; }' +
    '.gate-names { font-family: Italiana, serif; font-size: 30px; letter-spacing: .12em; text-indent: .12em;' +
    '  text-transform: uppercase; color: #1d1a16; margin: 12px 0 0; }' +
    '.gate-ask { font-family: "Cormorant Garamond", serif; font-style: italic; font-size: 17px;' +
    '  color: #6e665a; margin: 34px 0 0; }' +
    '.gate-input { display: block; width: 100%; max-width: 300px; margin: 18px auto 0; padding: 8px 2px;' +
    '  background: transparent; border: none; border-bottom: 1px solid rgba(29,26,22,.35);' +
    '  font-family: "Cormorant Garamond", serif; font-size: 19px; color: #1d1a16; text-align: center;' +
    '  border-radius: 0; outline: none; }' +
    '.gate-input:focus { border-bottom-color: #1d1a16; }' +
    '.gate-input::placeholder { color: rgba(110,102,90,.65); font-style: italic; font-size: 15px; }' +
    '.gate-btn { appearance: none; margin: 26px auto 0; display: inline-block; cursor: pointer;' +
    '  border: 1px solid #1d1a16; background: #1d1a16; color: #ece7d8; padding: 12px 30px;' +
    '  font-family: "Tenor Sans", sans-serif; font-size: 10.5px; letter-spacing: .3em; text-indent: .3em;' +
    '  text-transform: uppercase; transition: background .15s, color .15s; }' +
    '.gate-btn:hover { background: transparent; color: #1d1a16; }' +
    '.gate-btn:active { transform: translateY(1px); }' +
    '.gate-btn:focus-visible { outline: 1px solid #1d1a16; outline-offset: 3px; }' +
    '.gate-msg { font-family: "Cormorant Garamond", serif; font-style: italic; font-size: 14.5px;' +
    '  color: #6e665a; margin: 18px 0 0; min-height: 1.4em; text-wrap: balance; }';
  document.head.appendChild(style);

  function norm(s) {
    s = s.toLowerCase();
    try { s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, ''); } catch (e) {}
    return s.replace(/[^a-z]/g, '');
  }
  function sha(s) {
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(SALT + s)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) {
        return ('0' + b.toString(16)).slice(-2);
      }).join('');
    });
  }
  function admitted(raw) {
    var tokens = raw.trim().split(/\s+/).map(norm).filter(Boolean);
    var candidates = [norm(raw)];
    if (tokens.length >= 2) candidates.push(tokens[0] + tokens[tokens.length - 1]);
    return Promise.all(candidates.map(sha)).then(function (hashes) {
      return hashes.some(function (h) { return HASHES[h] === 1; });
    });
  }

  function build() {
    var gate = document.createElement('div');
    gate.className = 'gate';
    gate.setAttribute('role', 'dialog');
    gate.setAttribute('aria-modal', 'true');
    gate.setAttribute('aria-label', 'Invitation');
    gate.innerHTML =
      '<div class="gate-inner">' +
      '<img src="/assets/img/seal-emboss-lg.png" width="92" height="92" alt="" style="display:block;margin:0 auto">' +
      '<p class="gate-eyebrow">The wedding of</p>' +
      '<p class="gate-names">Chelsey &amp; Alex</p>' +
      '<p class="gate-ask">May we take your name?</p>' +
      '<form class="gate-form">' +
      '<input class="gate-input" type="text" name="name" autocomplete="name" autocapitalize="words"' +
      ' enterkeyhint="go" aria-label="Your name" placeholder="first name and surname">' +
      '<button class="gate-btn" type="submit">Enter</button>' +
      '</form>' +
      '<p class="gate-msg" role="status" aria-live="polite"></p>' +
      '</div>';
    document.body.appendChild(gate);
    var input = gate.querySelector('.gate-input');
    var msg = gate.querySelector('.gate-msg');
    gate.querySelector('.gate-form').addEventListener('submit', function (e) {
      e.preventDefault();
      var raw = input.value;
      if (!raw.trim()) return;
      admitted(raw).then(function (ok) {
        if (ok) {
          try {
            localStorage.setItem(KEY, '1');
            localStorage.setItem('ca-guest', raw.trim());
          } catch (err) {}
          var gn = document.getElementById('guest-name');
          if (gn && !gn.value) {
            gn.value = raw.trim();
            gn.dispatchEvent(new Event('input', { bubbles: true }));
          }
          msg.textContent = 'Do come in.';
          gate.querySelector('.gate-btn').disabled = true;
          setTimeout(function () {
            document.documentElement.classList.remove('gate-locked');
            gate.classList.add('gate-open');
            if (location.hash) {
              var t = document.getElementById(location.hash.slice(1));
              if (t) t.scrollIntoView();
            }
            var m = document.querySelector('main');
            if (m) { m.setAttribute('tabindex', '-1'); m.focus({ preventScroll: true }); }
            setTimeout(function () { gate.remove(); }, 800);
          }, 700);
        } else {
          msg.textContent = 'We cannot find that name. Do try your full name, or ask Chelsey or Alex.';
          input.select();
        }
      });
    });
    input.focus();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
