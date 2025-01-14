importScripts('https://www.gstatic.com/firebasejs/3.6.8/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/3.6.8/firebase-messaging.js');

const firebaseConfig = {
  apiKey: "AIzaSyBVdJXAzcESHNV92-NJIb1EcbKAph-74_c",
  authDomain: "provence-coffee.firebaseapp.com",
  projectId: "provence-coffee",
  storageBucket: "provence-coffee.firebasestorage.app",
  messagingSenderId: "915337719770",
  appId: "1:915337719770:web:48800e5ebe66025d729ae3",
  measurementId: "G-VETRKWCYR4"
};


// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();
const analytics = getAnalytics(app);

