import { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import InventoryList from "./pages/InventoryList.jsx";
import TaskList from "./pages/TaskList.jsx";
import SkuDetail from "./pages/SkuDetail.jsx";

const navItems = [
  { key: "dashboard", label: "Dashboard" },
  { key: "inventory", label: "Inventory" },
  { key: "tasks", label: "Tasks" },
];

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedSku, setSelectedSku] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const refreshAll = () => setReloadKey((value) => value + 1);

  const openInventory = () => {
    setSelectedSku(null);
    setActivePage("inventory");
  };

  const openSkuDetail = (sellerSku) => {
    setSelectedSku(sellerSku);
    setActivePage("skuDetail");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">Amazon Inventory Agent</div>
          <div className="subbrand">MVP operations dashboard</div>
        </div>
        <nav className="nav-tabs" aria-label="Primary">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={activePage === item.key ? "nav-tab active" : "nav-tab"}
              onClick={() => {
                setSelectedSku(null);
                setActivePage(item.key);
              }}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="page">
        {activePage === "dashboard" && (
          <Dashboard reloadKey={reloadKey} onAgentRun={refreshAll} />
        )}
        {activePage === "inventory" && (
          <InventoryList reloadKey={reloadKey} onSelectSku={openSkuDetail} />
        )}
        {activePage === "tasks" && (
          <TaskList reloadKey={reloadKey} onTaskUpdated={refreshAll} />
        )}
        {activePage === "skuDetail" && selectedSku && (
          <SkuDetail sellerSku={selectedSku} onBack={openInventory} />
        )}
      </main>
    </div>
  );
}

export default App;
