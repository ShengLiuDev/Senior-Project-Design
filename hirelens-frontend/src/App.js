import { useState, useEffect } from "react";
import Header from './Header';
function App() {
  const [testVar, setTestVar] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000")
      .then((response) => response.json())
      .then((data) => {
        setTestVar(data.message);
      })
      .catch((error) => console.error("Error fetching data:", error));
  }, []);

  return (
    <div className="app">
		<Header />
        <p>{testVar}</p>
		<div className="app-content">
              {'Dashboard'}
          </div>
    </div>
  );
}

export default App;