// server.js (Node.js with Express)
// ... (Your existing server-side code) ...

app.get("/user-session", (req, res) => {
  res.json({ userId: req.session.userId });
});

// ... (Your login, signup, and logout routes) ...
