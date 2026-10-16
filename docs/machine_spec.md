# สเปกเครื่องที่ใช้ประมวลผล (Machine Specification)

> เก็บข้อมูลจากเครื่องจริงเมื่อ 2026-10-12 ด้วย `lscpu`, `free`, `nvidia-smi`, `lsblk`, `dmidecode`
> งานทั้งหมดในโปรเจกต์นี้ประมวลผลบนเครื่องนี้เครื่องเดียว (single-node, local) โดยไม่ใช้ cluster

## 1. ภาพรวม

| รายการ | ค่า |
|---|---|
| รุ่นเครื่อง | MSI Katana 15 B13VFK (โน้ตบุ๊ก) |
| CPU | Intel Core i9-13900H — 14 คอร์ / 20 เธรด |
| RAM | 32 GB DDR5 (2 แถว, dual-channel) ทำงานที่ 5200 MT/s |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU — 8 GB GDDR6 |
| Storage | NVMe SSD Samsung PM9B1 1 TB (PCIe) |
| OS | Ubuntu 26.04.1 LTS, Linux kernel 7.0.0-38-generic |

## 2. CPU — Intel Core i9-13900H

| รายการ | ค่า |
|---|---|
| สถาปัตยกรรม | Raptor Lake (Intel 13th Gen), x86_64, Family 6 Model 186 Stepping 2 |
| โครงสร้าง | Hybrid: **6 Performance-cores** (มี Hyper-Threading → 12 เธรด) + **8 Efficient-cores** (8 เธรด) |
| รวม | 14 คอร์ / 20 เธรด, 1 socket, 1 NUMA node |
| ความถี่ | ต่ำสุด 0.4 GHz · สูงสุด 5.4 GHz |
| ความถี่สูงสุดแยกตามคอร์ (จาก `lscpu -e`) | 4 เธรด @ 5.4 GHz, 8 เธรด @ 5.2 GHz (P-core) · 8 เธรด @ 4.1 GHz (E-core) |
| L1d / L1i | 544 KiB (14 instances) / 704 KiB (14 instances) |
| L2 | 11.5 MiB (8 instances) |
| L3 | 24 MiB (shared) |
| ชุดคำสั่ง SIMD ที่สำคัญ | SSE4.2, **AVX2**, **FMA**, **AVX-VNNI**, F16C, BMI1/2, SHA-NI, AES-NI, VAES, GFNI |
| ไม่มี | AVX-512 |
| Virtualization | VT-x |
| CPU governor / platform profile | `powersave` (intel_pstate + HWP) / `performance` |

**ผลต่อการประมวลผล**
- DuckDB และ Polars เป็น engine แบบ vectorized ที่ใช้ AVX2 และกระจายงานได้ทุกเธรด จึงได้ประโยชน์จาก 20 เธรดโดยตรง
- คอร์ไม่เท่ากัน (P-core เร็วกว่า E-core) ทำให้การเพิ่มเธรดจาก 12 → 20 ได้ speedup ไม่เป็นเส้นตรง ควรวัดด้วย thread-scaling test
- L3 24 MiB ช่วยงาน hash aggregation/join ที่ตาราง hash เล็ก เช่น group by สถานี (~50 ค่า)

## 3. หน่วยความจำ (RAM)

| รายการ | ค่า |
|---|---|
| ชนิด | DDR5, non-ECC (`Error Correction Type: None`) |
| จำนวนแถว | 2 แถว → dual-channel |
| ความจุรวม | 32 GB (OS เห็น 30.6 GiB = 32,096,808 kB) |
| ความเร็วตามสเปกแรม | 5600 MT/s |
| ความเร็วที่ทำงานจริง (Configured) | **5200 MT/s** (ถูกจำกัดโดย memory controller ของ i9-13900H) |
| แบนด์วิดท์สูงสุดตามทฤษฎี | 5200 MT/s × 8 B × 2 ch ≈ **83.2 GB/s** |
| Swap | 8 GB (swap file `/swap.img`) |
| RAM ว่างขณะเก็บข้อมูล | ~25 GiB available |

**ผลต่อการประมวลผล**
- ข้อมูลดิบ (CSV 2.8 GB, ~112.5 ล้านแถว) และ Parquet ที่บีบอัดแล้วใส่ใน RAM ได้ทั้งหมด จึงไม่จำเป็นต้องใช้ cluster
- ตาราง OD เต็มเมื่อขยายเป็น pandas/object dtype อาจใช้ RAM หลายเท่าของขนาดไฟล์ จึงต้องใช้ dtype ที่เหมาะสม (Categorical/ENUM, UINT8, UINT16) และให้ DuckDB มี `memory_limit` เพื่อ spill ลง NVMe ได้

## 4. GPU — NVIDIA GeForce RTX 4060 Laptop GPU

| รายการ | ค่า |
|---|---|
| ชิป | AD107 (Max-Q / Mobile), สถาปัตยกรรม **Ada Lovelace** |
| Compute Capability | **8.9** |
| VRAM | **8 GB GDDR6** (8188 MiB) |
| Max Graphics / SM clock | 3105 MHz |
| Max Memory clock | 8001 MHz |
| PCIe | Gen 4 x8 (Bus 01:00.0) |
| Power limit (TGP) | ค่าเริ่มต้น 80 W · ปรับได้ 5 – 105 W |
| NVIDIA Driver | 595.91.07 |
| CUDA (driver รองรับ) | 13.2 |
| CUDA Toolkit (`nvcc`) | ไม่ได้ติดตั้ง — ใช้ CUDA runtime ที่มากับ Python wheel |
| VRAM ที่ desktop ใช้อยู่แล้ว | ~0.7 GB (GPU ตัวนี้ขับจอด้วย) → เหลือใช้งานจริง ~7.4 GB |

**ผลต่อการประมวลผล**
- เหมาะกับการเทรน gradient boosting (XGBoost/LightGBM `device="cuda"`) และงาน ML ที่ขนานได้มาก
- VRAM 8 GB เป็นข้อจำกัดหลัก ข้อมูลระดับ OD เต็มชุดต้องใช้ `QuantileDMatrix` หรือแบ่ง batch
- PCIe x8 ทำให้การโยกข้อมูลไปกลับ CPU↔GPU มีต้นทุน งานเล็กอาจเร็วบน CPU มากกว่า

## 5. Storage

| รายการ | ค่า |
|---|---|
| ไดรฟ์ | Samsung PM9B1 NVMe SSD 1 TB (รุ่น MZVL41T0HBLB-00BTW, **DRAM-less**) |
| พาร์ติชัน | `/boot/efi` 1 GB (vfat) · `/boot` 2 GB (ext4) · root 950.8 GB |
| Layer ของ root | **LUKS (dm-crypt)** → LVM → ext4 |
| พื้นที่ | 935 GB, ใช้ 133 GB, ว่าง 755 GB |

**ผลต่อการประมวลผล**
- ดิสก์เข้ารหัสทั้งลูก (AES; CPU มี AES-NI) จึงมี overhead ตอนอ่าน/เขียน
- SSD แบบ DRAM-less มีความเร็ว random I/O และการเขียนต่อเนื่องนานๆ ต่ำกว่ารุ่นที่มี DRAM
- ทั้งสองข้อเป็นเหตุผลที่การแปลง CSV → Parquet (zstd) ช่วยได้มาก เพราะอ่านข้อมูลจากดิสก์น้อยลงและอ่านเฉพาะคอลัมน์ที่ใช้

## 6. ซอฟต์แวร์

| รายการ | ค่า |
|---|---|
| OS | Ubuntu 26.04.1 LTS (Resolute Raccoon) |
| Kernel | Linux 7.0.0-38-generic (PREEMPT_DYNAMIC) |
| Python (ระบบ) | 3.14.4 |
| ตัวจัดการ environment | `uv` |
| Hostname | ubuntu-katana |

## 7. ชุดข้อมูลเทียบกับเครื่อง

| รายการ | ค่า |
|---|---|
| แหล่งข้อมูล | BART Origin-Destination ridership (http://64.111.127.166/origin-destination/) |
| ไฟล์ | CSV 13 ไฟล์ ปี 2011 – 2023 (ปี 2023 ถึง 2023-05-02) |
| ขนาด | ~2.8 GB (ไม่บีบอัด) |
| จำนวนแถว | **112,536,145** แถว (รวม header) |
| คอลัมน์ | Date, Hour, Origin Station, Destination Station, Trip Count |
| ขนาดข้อมูล / RAM | ~9% ของ RAM ทั้งหมด |

## 8. เงื่อนไขขณะ benchmark (ต้องคุมให้เหมือนกันทุกครั้ง)

- เสียบสายชาร์จตลอด (โน้ตบุ๊กลดความเร็ว CPU/GPU เมื่อใช้แบตเตอรี่)
- Platform profile = `performance`
- ปิดโปรแกรมหนักอื่นๆ (เบราว์เซอร์, เกม)
- รันแต่ละการทดสอบหลายรอบ (เช่น 5 รอบ) และรายงาน median ทั้งแบบ cold cache และ warm cache
  - ล้าง page cache สำหรับ cold run: `sync; echo 3 | sudo tee /proc/sys/vm/drop_caches`

## 9. คำสั่งที่ใช้เก็บข้อมูล (reproducible)

```bash
lscpu; lscpu -e=CPU,CORE,MAXMHZ
free -h; swapon --show
sudo dmidecode -t memory | grep -E "Speed|Type:"
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap,pcie.link.gen.max,pcie.link.width.max --format=csv
nvidia-smi -q -d CLOCK,POWER
lsblk -o NAME,SIZE,TYPE,ROTA,MODEL,FSTYPE,MOUNTPOINT; df -h /
cat /sys/class/dmi/id/product_name /sys/firmware/acpi/platform_profile
cat /etc/os-release; uname -a
wc -l data/raw/ridership/*.csv
```
