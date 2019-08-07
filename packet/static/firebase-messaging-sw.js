importScripts('https://www.gstatic.com/firebasejs/6.3.4/firebase-app.js')
importScripts('https://www.gstatic.com/firebasejs/6.3.4/firebase-messaging.js')

// This has to be a static value because it's a service worker
 firebase.initializeApp({
   'messagingSenderId': '937927597278'
 });

const messaging = firebase.messaging();