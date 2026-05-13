import uuid
import json
from datetime import datetime, timedelta
from core.database import SessionLocal, AgentRegistryModel

OFFLINE_THRESHOLD_MINUTES = 10

def register_agent(agent_name: str, capabilities: list, version: str, environment: str) -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        existing = db.query(AgentRegistryModel).filter(
            AgentRegistryModel.agent_name == agent_name
        ).first()

        if existing:
            existing.status = 'HEALTHY'
            existing.last_heartbeat = now
            existing.capabilities = json.dumps(capabilities)
            existing.version = version
            existing.environment = environment
            existing.updated_at = now
            db.commit()
            return {'status': 'updated', 'agent': agent_name}
        else:
            record = AgentRegistryModel(
                id=str(uuid.uuid4()),
                agent_name=agent_name,
                status='HEALTHY',
                last_heartbeat=now,
                capabilities=json.dumps(capabilities),
                version=version,
                environment=environment,
                last_error='',
                created_at=now,
                updated_at=now,
            )
            db.add(record)
            db.commit()
            return {'status': 'registered', 'agent': agent_name}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'detail': str(e)}
    finally:
        db.close()

def heartbeat_agent(agent_name: str, status: str, last_error: str = '') -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        agent = db.query(AgentRegistryModel).filter(
            AgentRegistryModel.agent_name == agent_name
        ).first()

        if not agent:
            return {'status': 'error', 'detail': 'Agent not registered'}

        agent.last_heartbeat = now
        agent.updated_at = now
        agent.status = status.upper()
        if last_error:
            agent.last_error = last_error
            agent.status = 'DEGRADED'
        db.commit()
        return {'status': 'ok', 'agent': agent_name}
    except Exception as e:
        db.rollback()
        return {'status': 'error', 'detail': str(e)}
    finally:
        db.close()

def get_agents_status() -> dict:
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        threshold = now - timedelta(minutes=OFFLINE_THRESHOLD_MINUTES)
        agents = db.query(AgentRegistryModel).all()

        result = {'healthy': [], 'offline': [], 'degraded': [], 'total': len(agents)}
        for a in agents:
            caps = []
            try:
                caps = json.loads(a.capabilities or '[]')
            except:
                pass

            info = {
                'agent_name': a.agent_name,
                'status': a.status,
                'version': a.version,
                'environment': a.environment,
                'capabilities': caps,
                'last_heartbeat': a.last_heartbeat.isoformat() if a.last_heartbeat else None,
                'last_error': a.last_error,
            }

            if a.last_heartbeat and a.last_heartbeat < threshold:
                info['status'] = 'OFFLINE'
            
            if info['status'] == 'HEALTHY':
                result['healthy'].append(info)
            elif info['status'] == 'DEGRADED':
                result['degraded'].append(info)
            else:
                result['offline'].append(info)

        return result
    except Exception as e:
        return {'error': str(e)}
    finally:
        db.close()