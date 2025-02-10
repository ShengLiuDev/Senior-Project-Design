import { useState, useEffect } from "react";

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
    <div className="App">
      <header className="App-header">
        <p>{testVar}</p>
      </header>
    </div>
  );
}

export default App;