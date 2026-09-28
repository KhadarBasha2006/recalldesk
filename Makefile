.PHONY: install hindsight seed api web test demo

install:
	cd backend && python -m pip install -r requirements.txt
	cd frontend && npm install

hindsight:
	docker run -it --pull always --name hindsight --restart unless-stopped \
		--shm-size=1g -p 8888:8888 -p 9999:9999 \
		-e HINDSIGHT_API_LLM_PROVIDER=groq \
		-e HINDSIGHT_API_LLM_API_KEY=$${GROQ_API_KEY:?set GROQ_API_KEY first} \
		-e HINDSIGHT_API_LLM_MODEL=openai/gpt-oss-120b \
		ghcr.io/vectorize-io/hindsight:latest

seed:
	cd backend && python ../scripts/seed_history.py

api:
	cd backend && uvicorn app.main:app --reload --port 8000

web:
	cd frontend && npm run dev

test:
	cd backend && pytest -v

demo: seed api
