// Paste this into the browser console on wanna.freeup.life
// AFTER capture_server.py is running on your Mac.
//
// Usage:  await captureShot('01_home')

(async function installCapture() {
  // Load html2canvas if not already present
  if (!window.html2canvas) {
    await new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }

  window.captureShot = async function(name) {
    console.log(`📸 Capturing ${name}…`);
    const canvas = await html2canvas(document.body, {
      width: 390, windowWidth: 390, scale: 2,
      useCORS: true, allowTaint: true,
      backgroundColor: '#faf7f2',
      scrollY: -window.scrollY
    });
    const b64 = canvas.toDataURL('image/jpeg', 0.88).split(',')[1];
    const resp = await fetch('http://localhost:8765/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name + '.jpg', image: b64 })
    });
    const json = await resp.json();
    console.log(`  ✓ ${name} saved (${Math.round(b64.length * 0.75 / 1024)}KB)`);
    return json;
  };

  console.log('✅ captureShot() ready. Example: await captureShot("01_home")');
})();
