"""Persistence for foundation."""
import json
import sqlite3

class Repository:
    def __init__(self,conn:sqlite3.Connection):self.conn=conn
    def create_task(self,description):
        title=description.strip().splitlines()[0][:120] or "Untitled"
        cur=self.conn.execute("INSERT INTO tasks(title,description) VALUES(?,?)",(title,description))
        self.conn.commit()
        return self.get_task(cur.lastrowid)
    def get_task(self,task_id):
        row=self.conn.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
        if row is None:return None
        result=dict(row)
        result["rounds"]=[]
        for rnd in self.conn.execute("SELECT * FROM rounds WHERE task_id=? ORDER BY round_number",(task_id,)):
            x=dict(rnd);x["selected_roles"]=json.loads(x["selected_roles"])
            x["role_outputs"]=[]
            for out in self.conn.execute("SELECT * FROM role_outputs WHERE round_id=? ORDER BY id",(x["id"],)):
                o=dict(out)
                o["model_errors"]=[dict(e) for e in self.conn.execute("SELECT * FROM model_errors WHERE round_id=? AND role=? ORDER BY id",(x["id"],o["role"]))]
                x["role_outputs"].append(o)
            result["rounds"].append(x)
        return result
    def get_round(self,round_id):
        row=self.conn.execute("SELECT * FROM rounds WHERE id=?",(round_id,)).fetchone()
        if row is None:return None
        x=dict(row);x["selected_roles"]=json.loads(x["selected_roles"])
        x["role_outputs"]=[dict(r) for r in self.conn.execute("SELECT * FROM role_outputs WHERE round_id=? ORDER BY id",(round_id,))]
        return x
    def create_round(self,task_id,selected_roles,user_comment):
        n=self.conn.execute("SELECT COALESCE(MAX(round_number),0) FROM rounds WHERE task_id=?",(task_id,)).fetchone()[0]+1
        cur=self.conn.execute("INSERT INTO rounds(task_id,round_number,user_comment,selected_roles) VALUES(?,?,?,?)",(task_id,n,user_comment,json.dumps(selected_roles,ensure_ascii=False)))
        self.conn.commit();return self.get_round(cur.lastrowid)
    def save_role_output(self,round_id,role,output,provider,model_id,status,response_time_ms):
        self.conn.execute("""INSERT INTO role_outputs(round_id,role,output,provider,model_id,status,response_time_ms) VALUES(?,?,?,?,?,?,?)
          ON CONFLICT(round_id,role) DO UPDATE SET output=excluded.output,provider=excluded.provider,model_id=excluded.model_id,status=excluded.status,response_time_ms=excluded.response_time_ms,updated_at=CURRENT_TIMESTAMP""",(round_id,role,output,provider,model_id,status,response_time_ms))
        self.conn.commit()
    def add_model_error(self,round_id,role,provider,model_id,error):
        self.conn.execute("INSERT INTO model_errors(round_id,role,provider,model_id,error) VALUES(?,?,?,?,?)",(round_id,role,provider,model_id,error));self.conn.commit()
    def update_model_status(self,provider,model_id,role,status,last_error="",response_time_ms=None):
        if status=="available":
            self.conn.execute("""INSERT INTO model_status(provider,model_id,role,status,last_error,last_success_at,response_time_ms) VALUES(?,?,?,?,'',CURRENT_TIMESTAMP,?)
            ON CONFLICT(provider,model_id,role) DO UPDATE SET status=excluded.status,last_error='',last_success_at=CURRENT_TIMESTAMP,response_time_ms=excluded.response_time_ms""",(provider,model_id,role,status,response_time_ms))
        else:
            self.conn.execute("""INSERT INTO model_status(provider,model_id,role,status,last_error,last_failure_at,response_time_ms) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP,?)
            ON CONFLICT(provider,model_id,role) DO UPDATE SET status=excluded.status,last_error=excluded.last_error,last_failure_at=CURRENT_TIMESTAMP,response_time_ms=excluded.response_time_ms""",(provider,model_id,role,status,last_error,response_time_ms))
        self.conn.commit()
    def list_model_status(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM model_status ORDER BY role,provider,model_id")]
    def update_round_summary(self,round_id,summary):
        self.conn.execute("UPDATE rounds SET summary=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(summary,round_id));self.conn.commit()
