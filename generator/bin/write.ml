(** Wraps a one-line C expression in a valid C program.*)
let program expr = 
  "#define false 0\n#define true 1\nint program(long long int x, long long int y) { return " ^ expr ^ "; }"

(** Takes filename and content. Writes the content to the file. *)
let write_file filename content = 
  let oc = open_out filename in
  Printf.fprintf oc "%s\n" content;
  close_out oc

