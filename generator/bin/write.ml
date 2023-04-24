let program seed expr = 
  "int seed = " ^ string_of_int seed ^ ";\nint program(int x, int y) { return " ^ expr ^ "; }"

let write_file filename content = 
  let oc = open_out filename in
  Printf.fprintf oc "%s\n" content;
  close_out oc

