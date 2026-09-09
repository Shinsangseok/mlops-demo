.PHONY: backend frontend ps down

backend:
	docker run -d \
		--name backend \
		-p 8000:8000 \
		--network mlops_demo_network \
		-v /root/summarize-app/models:/models \
		backend

frontend:
	docker run -d \
		--name frontend \
		-p 80:8501 \
		--network mlops_demo_network \
		frontend

ps:
	docker ps

down:
	docker rm -f backend frontend
