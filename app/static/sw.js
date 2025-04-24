self.addEventListener('install', function (event) {
    event.waitUntil(
        function(){
            console.log("SW: PWA installiert !");
        }
    );
});

self.addEventListener('fetch', function (event) {
    // Bisher kein Ressourcen Management nötig !
});