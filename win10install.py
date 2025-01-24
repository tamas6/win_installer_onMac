import os
import subprocess
import time

def run_command(command, success_message=""):
    """Run a shell command and handle errors."""
    try:
        print(f"🔄 Running: {command}")
        result = subprocess.run(command, shell=True, check=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if success_message:
            print(f"✅ {success_message}")
        return result.stdout.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr.decode('utf-8')}")
        exit(1)

def list_iso_files():
    """List all .iso files in the current directory."""
    current_dir = os.getcwd()
    iso_files = [f for f in os.listdir(current_dir) if f.endswith('.iso')]
    return iso_files

def list_disks():
    """List all available disks."""
    print("\n🔍 Fetching available disks...")
    disk_list = run_command("diskutil list", "Available disks listed.")
    return disk_list

def select_from_list(options, prompt):
    """Display a list of options and let the user select one."""
    print("\n📂 Available options:")
    for idx, option in enumerate(options, start=1):
        print(f"{idx}. {option}")
    while True:
        try:
            choice = int(input(f"\n{prompt} "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def estimate_time(iso_size_mb, write_speed_mb_s):
    """Estimate the time to write the ISO to the USB based on size and speed."""
    if write_speed_mb_s > 0:
        return iso_size_mb / write_speed_mb_s
    return float('inf')  # Prevent division by zero

def create_bootable_usb(iso_path, usb_disk):
    """Create a bootable USB drive."""
    print("\n💾 Writing ISO to the USB drive. This process may take several minutes...")

    # Get file size for estimation
    iso_size_mb = os.path.getsize(iso_path) / (1024 * 1024)
    
    start_time = time.time()
    dd_process = subprocess.Popen(
        f"sudo dd if={iso_path} of={usb_disk} bs=4M status=progress",
        shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE
    )

    # Monitor progress
    write_speed_mb_s = 0.0
    for line in dd_process.stderr:
        decoded_line = line.decode('utf-8')
        print(decoded_line.strip())
        if "bytes transferred" in decoded_line:
            parts = decoded_line.split(",")
            for part in parts:
                if "MB/s" in part:
                    write_speed_mb_s = float(part.split("MB/s")[0].strip())
                    break
            if write_speed_mb_s > 0:
                remaining_time = estimate_time(iso_size_mb, write_speed_mb_s)
                print(f"⏳ Estimated time remaining: {remaining_time:.2f} seconds")

    dd_process.wait()
    end_time = time.time()

    print(f"\n✅ Writing complete! Time taken: {end_time - start_time:.2f} seconds.")

    print("\n💾 Finalizing the process...")
    run_command("sync", "Data successfully written to the USB drive.")
    run_command(f"diskutil eject {usb_disk}", "USB drive ejected successfully.")

    print("\n🎉 Bootable USB installer created successfully!")

if __name__ == "__main__":
    print("🔍 Detecting available .iso files...")
    iso_files = list_iso_files()
    if not iso_files:
        print("❌ No .iso files found in the current directory.")
        exit(1)
    iso_choice = select_from_list(iso_files, "Select an ISO file to use:")

    print("\n🔍 Listing available disks...")
    disks_info = list_disks()
    print(disks_info)
    usb_disk = input("💾 Enter the device identifier for your USB disk (e.g., /dev/disk3): ").strip()

    print("\n🚀 Creating bootable USB...")
    create_bootable_usb(iso_choice, usb_disk)
