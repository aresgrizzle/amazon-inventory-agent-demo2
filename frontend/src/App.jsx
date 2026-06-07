import { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import InventoryList from "./pages/InventoryList.jsx";
import ProblemDetail from "./pages/ProblemDetail.jsx";
import TaskList from "./pages/TaskList.jsx";
import SkuDetail from "./pages/SkuDetail.jsx";

const navItems = [
  { key: "dashboard", label: "经营看板" },
  { key: "inventory", label: "库存诊断" },
  { key: "tasks", label: "运营待办" },
];

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [selectedSku, setSelectedSku] = useState(null);
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [reloadKey, setReloadKey] = useState(0);

  const refreshAll = () => setReloadKey((value) => value + 1);

  const openInventory = () => {
    setSelectedSku(null);
    setSelectedInsight(null);
    setActivePage("inventory");
  };

  const openSkuDetail = (sellerSku) => {
    setSelectedInsight(null);
    setSelectedSku(sellerSku);
    setActivePage("skuDetail");
  };

  const openProblemDetail = (insight) => {
    setSelectedSku(null);
    setSelectedInsight(insight);
    setActivePage("problemDetail");
  };

  const openTasks = () => {
    setSelectedSku(null);
    setSelectedInsight(null);
    setActivePage("tasks");
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">亚马逊库存 Agent</div>
          <div className="subbrand">跨境电商库存运营工作台</div>
        </div>
        <nav className="nav-tabs" aria-label="主导航">
          {navItems.map((item) => (
            <button
              key={item.key}
              className={activePage === item.key ? "nav-tab active" : "nav-tab"}
              onClick={() => {
                setSelectedSku(null);
                setSelectedInsight(null);
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
          <TaskList
            reloadKey={reloadKey}
            onTaskUpdated={refreshAll}
            onSelectInsight={openProblemDetail}
          />
        )}
        {activePage === "skuDetail" && selectedSku && (
          <SkuDetail sellerSku={selectedSku} onBack={openInventory} />
        )}
        {activePage === "problemDetail" && (
          <ProblemDetail insight={selectedInsight} onBack={openTasks} />
        )}
      </main>
    </div>
  );
}

export default App;
