# frozen_string_literal: true

require 'json'
STDOUT.sync = true

begin
  require 'rouge'
  puts JSON.generate(ready: true, version: Rouge.version, styles: Rouge::Theme.registry.keys.sort)
rescue LoadError => error
  puts JSON.generate(ready: false, error: error.message)
  exit 1
end

formatter = Rouge::Formatters::HTML.new

ARGF.each_line do |line|
  next if line.strip.empty?

  begin
    request = JSON.parse(line)
    case request['operation']
    when 'highlight'
      code = request.fetch('code')
      lexer = Rouge::Lexer.find_fancy(request['language'].to_s.downcase, code)
      if !lexer && request['filename']
        begin
          lexer = Rouge::Lexer.guess(filename: request['filename'], source: code).new
        rescue Rouge::Guesser::Ambiguous
          lexer = nil
        end
      end
      lexer ||= Rouge::Lexers::PlainText.new
      value = formatter.format(lexer.lex(code))
    when 'css'
      theme = Rouge::Theme.find(request.fetch('style'))
      raise "unknown Rouge style: #{request['style']}" unless theme

      value = theme.render(scope: request.fetch('scope'))
    else
      raise "unknown operation: #{request['operation']}"
    end
    puts JSON.generate(ok: true, value: value)
  rescue StandardError => error
    puts JSON.generate(ok: false, error: error.message)
  end
end
