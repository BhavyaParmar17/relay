import { useCallback, useState } from "react";
import { Footer, TopBar } from "./components/Chrome.jsx";
import Hero from "./components/Hero.jsx";
import Steps from "./components/Steps.jsx";
import Studio from "./components/Studio.jsx";
import TraceStory from "./components/TraceStory.jsx";
import Rules from "./components/Rules.jsx";

export default function App() {
  const [request, setRequest] = useState(null);
  const handled = useCallback(() => setRequest(null), []);
  return (
    <>
      <a href="#studio" className="skip-link">Skip to the studio</a>
      <TopBar />
      <main>
        <Hero onStart={setRequest} />
        <Steps />
        <Studio request={request} onRequestHandled={handled} />
        <TraceStory />
        <Rules />
      </main>
      <Footer />
    </>
  );
}
