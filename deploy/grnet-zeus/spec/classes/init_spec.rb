require 'spec_helper'
describe 'zeus' do

  context 'with defaults for all parameters' do
    it { should contain_class('zeus') }
  end
end
