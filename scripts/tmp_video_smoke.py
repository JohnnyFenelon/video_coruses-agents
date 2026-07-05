import asyncio, pathlib, json, sys
from importlib import util
root = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(root))
spec = util.spec_from_file_location('vpmod', root/'backend'/'modes'/'video_production.py')
mod = util.module_from_spec(spec)
spec.loader.exec_module(mod)
pipe = mod.VideoProductionPipeline()

# Provide minimal blueprint with short story and style
blueprint = {'story':'A tiny comet befriends a paintbrush and saves the night skies.','style':'cinematic_realism'}

# Replace orchestrator.chat to return deterministic JSON for script and shots
async def fake_chat(prompt):
    if 'Write a cinematic video script' in prompt:
        return {'result': json.dumps({'title':'Test Story','logline':'A short test','style':'cinematic_realism','characters':[{'name':'Leo','description':'A child'}],'scenes':[{'scene_number':1,'location':'Workshop','time_of_day':'night','summary':'Intro','dialogue':'...','emotional_beat':'hope','duration_seconds':5}] ,'duration_estimate_seconds':60})}
    if 'Generate a character design sheet' in prompt:
        return {'result': json.dumps({'character_name':'Leo','style':'cinematic_realism','front_view_prompt':'front','side_view_prompt':'side','back_view_prompt':'back','expression_prompts':{'happy':'...'},'consistency_keywords':['bright']})}
    if 'Generate a video generation prompt for shot' in prompt:
        return {'result': json.dumps({'shot_id':1,'scene':1,'second':1,'camera_angle':'medium','lighting':'natural','action_description':'Leo paints','prompt':'paint prompt'})}
    return {'result': '{}'}

# Patch orchestrator
mod.orchestrator = type('O', (), {'chat': fake_chat})

async def run():
    res = await pipe.run(blueprint)
    print('Run result keys:', list(res.keys()))
    p = pathlib.Path(res['project_path'])/ 'export.json'
    print('Export exists:', p.exists())
    if p.exists():
        print(p.read_text()[:400])

asyncio.run(run())
