
def parse_hash(text):
  import re
  lines = text.split("\n")
  parsed = []
  for ln in lines:
    hash_regex = re.compile(r"([a-f0-9]{40})")
    m = hash_regex.search(ln)
    if not m: continue
    hash_value = m.group(1)  
    filepath = ln.replace(hash_value, "").strip()
    parsed.append((hash_value, filepath))
  return parsed

def find_tagged_cell(nb_cells, tag_text):
  cell_outputs = []
  for nb_cell in nb_cells:
    metadata = nb_cell.get('metadata', {})
    tags = metadata.get('tags', [])
    if tag_text in tags:
      outputs = nb_cell.get("outputs", [])
      for output_x in outputs:
        if output_x.get("output_type") == "stream":
          cell_outputs.append(output_x.get("text", ""))
    
  return cell_outputs

def find_section(nb_cells, header_text):
  section_buffer = []
  header_found = False
  for nb_cell in nb_cells:
    # if it's a markdown cell, check whether it's a section header
    if nb_cell.get("cell_type") == "markdown":
      md_text = nb_cell.get("source", "")

      # ignore non-header blocks
      if not md_text.startswith("#"):
        continue

      # we found another header block, 
      # This is the end of the target section. Break the loop
      else:        
        if header_found:
          break
      
      # check the section header, update the flag if we find it
      if header_text in md_text.lower():
        header_found = True
        continue    

    # accumulate the output of the cells after the header 
    if header_found:
      outputs = nb_cell.get("outputs", [])
      outputs = [x for x in outputs if x.get("output_type") == "stream"]
      section_buffer.extend([x.get("text", "") for x in outputs])
      header_found = True

  return section_buffer
