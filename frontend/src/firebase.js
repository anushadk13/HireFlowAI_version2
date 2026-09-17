import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyD8XMWy4BHzDglpXWrCu15gPIpRuRY7e2g",
  authDomain: "hireflowai-9bd8c.firebaseapp.com",
  projectId: "hireflowai-9bd8c",
  storageBucket: "hireflowai-9bd8c.firebasestorage.app",
  messagingSenderId: "829038126579",
  appId: "1:829038126579:web:89dec293b8128473981e86",
  measurementId: "G-ML184W5QPM",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

googleProvider.setCustomParameters({
  prompt: "select_account",
});

let analytics = null;

if (typeof window !== "undefined") {
  try {
    analytics = getAnalytics(app);
  } catch {
    analytics = null;
  }
}

export { app, analytics, auth, googleProvider };
