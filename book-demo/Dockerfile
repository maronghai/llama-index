FROM python:3.12-slim
WORKDIR /app
COPY install.py /app/install.py
RUN python install.py && useradd --uid 10001 --create-home kb && mkdir -p /data && chown kb:kb /data
COPY kb /app/kb
COPY run.py /app/run.py
USER 10001
ENV KB_DB=/data/knowledge.db KB_BIND=0.0.0.0
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready',timeout=3)"
CMD ["python", "run.py", "serve"]
