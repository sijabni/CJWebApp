import os
import json
import pyodbc
import logging
import azure.functions as func

app = func.FunctionApp()

@app.route(route="get_portfolio", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    # 1. Parse JSON safely
    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    # 2. Get Connection String correctly
    conn_str = os.environ.get("AzureSqlConnectionString")
    conn = pyodbc.connect(conn_str)
    if not conn_str:
        return func.HttpResponse("Connection string missing.", status_code=500)
    
    conn = None
    try:
        # 3. Use 'with' to auto-close the connection
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT Ticker, Shares, PurchasePrice FROM Portfolio")
            rows = cursor.fetchall()
            
            portfolio_list = []
            for row in cursor:
                current_price = 200.00  # Mock price
                # Safe conversion
                bought_at = float(row.PurchasePrice) if row.PurchasePrice else 0.0
                shares = float(row.Shares) if row.Shares else 0.0
                gain_loss = round((current_price - bought_at) * shares, 2)
                
                portfolio_list.append({
                    "ticker": row.Ticker,
                    "shares": shares,
                    "gain_loss": gain_loss
                })

            return func.HttpResponse(
                json.dumps(portfolio_list),
                mimetype="application/json",
                status_code=200
            )

    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return func.HttpResponse("Error accessing database.", status_code=500)
    
    finally:
        # 5. THE FIX: Explicitly close the connection
        if conn:
            conn.close() 
