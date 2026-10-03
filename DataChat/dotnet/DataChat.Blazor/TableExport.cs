using System.IO.Compression;
using System.Security;
using System.Text;
using System.Text.Json;

namespace DataChat.Blazor;

/// <summary>Builds CSV and Excel files from an answer's table. Numbers stay numbers so they can be totalled.</summary>
public static class TableExport
{
    public static byte[] Csv(IReadOnlyList<ColumnInfo> columns, IReadOnlyList<List<JsonElement>> rows)
    {
        var sb = new StringBuilder();
        sb.AppendLine(string.Join(",", columns.Select(c => CsvField(c.Label))));
        foreach (var row in rows)
        {
            sb.AppendLine(string.Join(",", columns.Select((_, i) => i < row.Count ? CsvCell(row[i]) : "")));
        }
        // with the byte order mark Excel reads ₹ and Hindi/Marathi text correctly
        return [.. Encoding.UTF8.GetPreamble(), .. Encoding.UTF8.GetBytes(sb.ToString())];
    }

    public static byte[] Xlsx(IReadOnlyList<ColumnInfo> columns, IReadOnlyList<List<JsonElement>> rows, string sheetName)
    {
        using var ms = new MemoryStream();
        using (var zip = new ZipArchive(ms, ZipArchiveMode.Create, leaveOpen: true))
        {
            Add(zip, "[Content_Types].xml",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
                "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">" +
                "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>" +
                "<Default Extension=\"xml\" ContentType=\"application/xml\"/>" +
                "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>" +
                "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>" +
                "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>" +
                "</Types>");
            Add(zip, "_rels/.rels",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
                "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
                "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>" +
                "</Relationships>");
            Add(zip, "xl/workbook.xml",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
                "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" " +
                "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">" +
                $"<sheets><sheet name=\"{Xml(SheetName(sheetName))}\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>");
            Add(zip, "xl/_rels/workbook.xml.rels",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
                "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
                "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>" +
                "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>" +
                "</Relationships>");
            // style 1 = bold header, 2 = #,##0.00 (money), 3 = #,##0 (whole numbers)
            Add(zip, "xl/styles.xml",
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
                "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">" +
                "<fonts count=\"2\"><font><sz val=\"11\"/><name val=\"Calibri\"/></font><font><b/><sz val=\"11\"/><name val=\"Calibri\"/></font></fonts>" +
                "<fills count=\"2\"><fill><patternFill patternType=\"none\"/></fill><fill><patternFill patternType=\"gray125\"/></fill></fills>" +
                "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>" +
                "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>" +
                "<cellXfs count=\"4\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/>" +
                "<xf numFmtId=\"0\" fontId=\"1\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyFont=\"1\"/>" +
                "<xf numFmtId=\"4\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyNumberFormat=\"1\"/>" +
                "<xf numFmtId=\"3\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\" applyNumberFormat=\"1\"/></cellXfs>" +
                "<cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles>" +
                "</styleSheet>");
            Add(zip, "xl/worksheets/sheet1.xml", Sheet(columns, rows));
        }
        return ms.ToArray();
    }

    private static string Sheet(IReadOnlyList<ColumnInfo> columns, IReadOnlyList<List<JsonElement>> rows)
    {
        var sb = new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>" +
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><cols>");
        for (var i = 0; i < columns.Count; i++)
        {
            sb.Append($"<col min=\"{i + 1}\" max=\"{i + 1}\" width=\"{Math.Clamp(columns[i].Label.Length + 4, 12, 50)}\" customWidth=\"1\"/>");
        }
        sb.Append("</cols><sheetData><row r=\"1\">");
        foreach (var c in columns)
        {
            sb.Append($"<c t=\"inlineStr\" s=\"1\"><is><t>{Xml(c.Label)}</t></is></c>");
        }
        sb.Append("</row>");
        for (var r = 0; r < rows.Count; r++)
        {
            sb.Append($"<row r=\"{r + 2}\">");
            for (var i = 0; i < columns.Count && i < rows[r].Count; i++)
            {
                var v = rows[r][i];
                if (v.ValueKind == JsonValueKind.Number)
                {
                    var style = columns[i].Format switch { "currency" => " s=\"2\"", "integer" => " s=\"3\"", _ => "" };
                    sb.Append($"<c{style}><v>{v.GetRawText()}</v></c>");
                }
                else if (v.ValueKind is not (JsonValueKind.Null or JsonValueKind.Undefined))
                {
                    var text = v.ValueKind == JsonValueKind.String ? v.GetString() ?? "" : v.GetRawText();
                    sb.Append($"<c t=\"inlineStr\"><is><t xml:space=\"preserve\">{Xml(text)}</t></is></c>");
                }
                else
                {
                    sb.Append("<c/>");
                }
            }
            sb.Append("</row>");
        }
        sb.Append("</sheetData></worksheet>");
        return sb.ToString();
    }

    private static void Add(ZipArchive zip, string name, string content)
    {
        using var w = new StreamWriter(zip.CreateEntry(name, CompressionLevel.Fastest).Open(), new UTF8Encoding(false));
        w.Write(content);
    }

    private static string CsvCell(JsonElement v) => v.ValueKind switch
    {
        JsonValueKind.Number => v.GetRawText(),
        JsonValueKind.Null or JsonValueKind.Undefined => "",
        JsonValueKind.String => CsvField(v.GetString() ?? ""),
        _ => CsvField(v.GetRawText()),
    };

    private static string CsvField(string s)
    {
        // a text starting with = + - @ would run as a formula in Excel
        if (s.Length > 0 && "=+-@\t\r".Contains(s[0])) s = "'" + s;
        return s.IndexOfAny([',', '"', '\n', '\r']) >= 0 ? "\"" + s.Replace("\"", "\"\"") + "\"" : s;
    }

    private static string Xml(string s)
    {
        var clean = new string(s.Where(ch => ch is '\t' or '\n' or '\r' || ch >= ' ').ToArray());
        return SecurityElement.Escape(clean) ?? "";
    }

    private static string SheetName(string s)
    {
        var name = new string(s.Where(ch => !"[]:*?/\\".Contains(ch)).ToArray()).Trim();
        return name.Length == 0 ? "Data" : name[..Math.Min(name.Length, 31)];
    }

    public static string FileName(string question, string extension)
    {
        var slug = new string(question.ToLowerInvariant().Select(ch => char.IsLetterOrDigit(ch) ? ch : '-').ToArray());
        while (slug.Contains("--")) slug = slug.Replace("--", "-");
        slug = slug.Trim('-');
        if (slug.Length > 60) slug = slug[..60].TrimEnd('-');
        return $"{(slug.Length == 0 ? "datachat" : slug)}-{DateTime.Now:yyyyMMdd-HHmm}.{extension}";
    }
}
