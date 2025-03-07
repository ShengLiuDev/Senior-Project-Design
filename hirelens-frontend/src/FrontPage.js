import { useState, useEffect } from "react";
import { Link } from 'react-router-dom';
import Header from './Header';
import './FrontPage.css';
function FrontPage() {
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
    <div>
		<Header />

		<div className="app-content" style={{fontSize:'32px'}}>
            HireLens
		</div>
		<div className="app-content" style={{fontSize:'28px'}}>
            "From students, for students, by students"
		</div>
		<Link className="app-content" to="/Test">
            Get started
		</Link>
 </div>
  );
}

export default FrontPage;