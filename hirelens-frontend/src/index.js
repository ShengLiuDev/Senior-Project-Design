import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import FrontPage from './FrontPage';
import Login from './Login';

export default function Layout() {
	return (
		<BrowserRouter>
		<Routes>
			<Route path="/" element={<FrontPage/>}/>
			<Route path="/Login" element = {<Login/>}/>
			<Route path="/ScoreHomepage" element = {<ScoreHomepage/>}/>
			<Route path="/CreateAccount" element = {<CreateAccount/>}/>
		</Routes>
		</BrowserRouter>
	);
}
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Layout/>
);
