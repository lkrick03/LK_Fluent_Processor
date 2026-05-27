import re

with open('vel_jou_export.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject Configuration Block
config_block = """# --- 5. Post-Processing Settings ---
# Airfoil Wall Surfaces
AIRFOIL_WALL_INSTANCES = [1, 2, 3, 20, 21, 22, 23, 24, 32, 33, 34, 35, 36]
AIRFOIL_SURFACE_TEMPLATE = "wall-enclosure-enclosure_instance_{}_solid1"

# Format: { "fluent-variable-name": "output-label" }
EXPORT_VARIABLES = {
    "pressure-coefficient": "Cp",
    "yplus": "Yplus",
    "skin-friction-coef": "Skin_Friction",
}
PLOT_DIRECTION = "1 0 0"

EXPORT_PATHLINES = False    
PATHLINE_VARIABLES = ["velocity-magnitude"]
PATHLINE_RELEASE_SURFACES = None

EXPORT_RESIDUALS = True

# TUI Command Strings"""

text = text.replace("# TUI Command Strings", config_block)


# 2. Inject Helper Functions above generate_journal_content()
helpers = """def get_airfoil_surfaces():
    return [AIRFOIL_SURFACE_TEMPLATE.format(i) for i in AIRFOIL_WALL_INSTANCES]

def _build_residual_scheme_for_velocity(res_file, mach):
    names_list = (
        '"continuity" "x-velocity" "y-velocity" "z-velocity" '
        '"energy" "k" "omega" "epsilon" "nut"'
    )

    scheme = f\"\""; --- Residual Export (Scheme) for Mach = {mach} ---
(display "  Exporting residuals for Mach = {mach}...\\\\n")
(let ((port (open-output-file "{res_file}"))
      (iters (residual-history "iteration"))
      (names '())
      (datas '()))
  (for-each
    (lambda (name)
      (let ((d (residual-history name)))
        (if (and (pair? d) (> (length d) 0))
          (begin
            (set! names (append names (list name)))
            (set! datas (append datas (list d)))))))
    (list {names_list}))
  (display "iteration" port)
  (for-each (lambda (nm) (display "\\\\t" port) (display nm port)) names)
  (newline port)
  (let ((n (length iters)))
    (do ((i 0 (+ i 1)))
        ((>= i n))
      (display (list-ref iters i) port)
      (for-each (lambda (d) (display "\\\\t" port) (display (list-ref d i) port)) datas)
      (newline port)))
  (close-output-port port)
  (display (format #f "    Wrote ~a iterations x ~a residuals to file\\\\n" (length iters) (length names))))

\"\"\"
    return scheme

def generate_journal_content():"""

text = text.replace("def generate_journal_content():", helpers)


# 3. Inject variables generation before the Mach loop
mach_loop_pre = """    # Prepare post-processing constants
    surfaces = get_airfoil_surfaces()
    surface_tui_string = " ".join(surfaces)
    pl_surfaces = PATHLINE_RELEASE_SURFACES if PATHLINE_RELEASE_SURFACES else surfaces
    pl_surface_tui = " ".join(pl_surfaces)

    # Iterate through each Mach number
    for mach in mach_values:"""

text = text.replace("    # Iterate through each Mach number\n    for mach in mach_values:", mach_loop_pre)


# 4. Inject post-processing chunk straight after Save Block
# Find the exact Save Block formulation
save_block = """{save_block}
\"\"\""""

post_process_chunk = """{save_block}
\"\"\"

        # --- POST PROCESSING ---
        if not TEST_MODE:
            post_block = f\"\"\"
; Ensure post-process dir exists
(ensure-directory (format #f "~a/y_plus_pressure_data" current-mach-dir))
\"\"\"
            for var_name, label in EXPORT_VARIABLES.items():
                output_file = f"{BASE_OUTPUT_DIR}/Mach_{mach}/y_plus_pressure_data/{OUTPUT_FILENAME_BASE}.{mach}.{label}.xy"
                output_file = output_file.replace("\\\\", "/")
                
                post_block += f\"\"\"; Export {label}
(display "  Exporting {label} for Mach = {mach}...\\\\n")
(ti-menu-load-string (format #f "/plot/plot yes \\\\"{output_file}\\\\" no no no {var_name} yes {PLOT_DIRECTION} {surface_tui_string} ()"))

\"\"\"
            if EXPORT_PATHLINES:
                for pl_var in PATHLINE_VARIABLES:
                    pl_label = pl_var.replace("-", "_")
                    pl_file = f"{BASE_OUTPUT_DIR}/Mach_{mach}/pathline_data/{OUTPUT_FILENAME_BASE}.{mach}.pathline.{pl_label}.fvp"
                    pl_file = pl_file.replace("\\\\", "/")
                    
                    post_block += f\"\"\"; --- Pathline Export: {pl_var} ---
(ensure-directory (format #f "~a/pathline_data" current-mach-dir))
(display "  Exporting pathlines ({pl_var}) for Mach = {mach}...\\\\n")
(ti-menu-load-string (format #f "/display/path-lines/write-to-files standard \\\\"{pl_file}\\\\" {pl_var} {pl_surface_tui} ()"))

\"\"\"
            if EXPORT_RESIDUALS:
                res_file = f"{BASE_OUTPUT_DIR}/Mach_{mach}/y_plus_pressure_data/{OUTPUT_FILENAME_BASE}.{mach}.residuals.csv"
                res_file = res_file.replace("\\\\", "/")
                post_block += _build_residual_scheme_for_velocity(res_file, mach)
                
            journal_content += post_block"""

text = text.replace(save_block, post_process_chunk)


with open('vel_jou_export.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Merge completed successfully.")
