import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import FrontPage from './FrontPage';
import Test from './Test';

export default function Layout() {
	return (
		<BrowserRouter>
		<Routes>
			<Route path="/" element={<FrontPage/>}/>
			<Route path="/Test" element = {<Test/>}/>
		</Routes>
		</BrowserRouter>
	);
}
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Layout/>
);
