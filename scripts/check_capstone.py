import capstone

# If capstone is available or let's use a simple disassembler or capstone
try:
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    has_capstone = True
except ImportError:
    has_capstone = False

print("has_capstone:", has_capstone)
