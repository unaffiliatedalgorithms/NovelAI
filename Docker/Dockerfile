FROM ubuntu

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl wget software-properties-common && \
    apt-get clean

# Add ROCm repository and install ROCm tools
RUN wget https://repo.radeon.com/amdgpu-install/7.0.1/ubuntu/noble/amdgpu-install_7.0.1.70001-1_all.deb
RUN apt-get update && apt install -y ./amdgpu-install_7.0.1.70001-1_all.deb
RUN amdgpu-install -y --usecase=rocm,rocmdev,hiplibsdk


#RUN wget -qO - http://repo.radeon.com/rocm/rocm.gpg.key | apt-key add - && \
#    echo "deb [arch=amd64] http://repo.radeon.com/rocm/apt/latest ubuntu main" > /etc/apt/sources.list.d/rocm.list && \
#    apt-get update && apt-get install -y rocminfo && \
#    apt-get clean

# Add pip, wheel and torch

RUN apt install python3-pip -y
RUN wget https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4.2/torch-2.6.0%2Brocm6.4.2.git76481f7c-cp312-cp312-linux_x86_64.whl
RUN wget https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4.2/torchvision-0.21.0%2Brocm6.4.2.git4040d51f-cp312-cp312-linux_x86_64.whl
RUN wget https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4.2/pytorch_triton_rocm-3.2.0%2Brocm6.4.2.git7e948ebf-cp312-cp312-linux_x86_64.whl
RUN wget https://repo.radeon.com/rocm/manylinux/rocm-rel-6.4.2/torchaudio-2.6.0%2Brocm6.4.2.gitd8831425-cp312-cp312-linux_x86_64.whl
RUN pip3 install --break-system-packages torch-2.6.0+rocm6.4.2.git76481f7c-cp312-cp312-linux_x86_64.whl torchvision-0.21.0+rocm6.4.2.git4040d51f-cp312-cp312-linux_x86_64.whl torchaudio-2.6.0+rocm6.4.2.gitd8831425-cp312-cp312-linux_x86_64.whl pytorch_triton_rocm-3.2.0+rocm6.4.2.git7e948ebf-cp312-cp312-linux_x86_64.whl
RUN pip3 install --break-system-packages transformers
RUN pip3 install --break-system-packages bitsandbytes
# hopefully the future bitsandbytes will support rocm in the default pip install
#RUN pip3 install --break-system-packages 'https://github.com/bitsandbytes-foundation/bitsandbytes/releases/download/continuous-release_multi-backend-refactor/bitsandbytes-0.44.1.dev0-py3-none-manylinux_2_24_x86_64.whl'
RUN pip3 install --break-system-packages gguf
RUN pip3 install --break-system-packages accelerate
# Enable ROCm
# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for ROCm compilers
# AMDGPU
ARG AMDGPU=gfx1100
#ENV HIPCXX="$(hipconfig -l)/clang"
ENV CC=/opt/rocm/llvm/bin/amdclang
ENV CXX=/opt/rocm/llvm/bin/amdclang++
RUN export HIPCXX="$(hipconfig -l)/clang" && export HIP_PATH="$(hipconfig -R)" && CMAKE_ARGS="-D GGML_HIP=on -D GGML_CPU_AARCH64=0 -D AMDGPU_TARGETS=$AMDGPU" pip3 install --verbose --upgrade --force-reinstall --no-cache-dir --break-system-packages llama-cpp-python
#RUN export HIPCXX="$(hipconfig -l)/clang" && export HIP_PATH="$(hipconfig -R)" && CMAKE_ARGS="-D GGML_HIPBLAS=on -D AMDGPU_TARGETS=$AMDGPU" pip3 install --verbose --upgrade --force-reinstall --no-cache-dir --break-system-packages llama-cpp-python==0.3.1
# Other utility tools
RUN pip3 install --break-system-packages -U "huggingface_hub[cli]"
RUN apt-get update && apt install -y nano
# Database tools
RUN pip3 install --break-system-packages sentence-transformers
RUN pip3 install --break-system-packages fasttext
#RUN pip3 install --break-system-packages faiss-cpu
RUN apt-get update && apt-get install -y \
    postgresql postgresql-contrib libpq-dev postgresql-server-dev-all\
    &&  pip3 install --break-system-packages psycopg2
# postgresql database initialization
RUN git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git && cd pgvector && make && make install
RUN pip3 install --break-system-packages pgvector
COPY postgresql_bash.sh /usr/local/bin/postgresql_bash.sh
CMD ["postgresql_bash.sh"]
